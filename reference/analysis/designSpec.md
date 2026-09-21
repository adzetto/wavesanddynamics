# wavesanddata.com — Build-Ready Design Spec (Astro static site)

**Source of truth:** 7 phone clips + 1 still of two successive drafts, each read twice and attacked by two adversarial critics. Where they disagree I rule below. All absolute pixel figures in the source reads are photo pixels misreported as CSS pixels — **every number in this spec is a chosen CSS value derived from measured *ratios*, not a measurement.** Build from this, not from the raw reads.

**Before building anything:** the original project is recoverable. Conversation title `Build webpage with provided files`, project name `Korkut's Research Hub`, artifact id `project:34000a66-3304-4430-a914-5c4a1656cce7`, chat uuid `9994de28-52ce-4af7-8d44-37ec65de63bb`. (v02 read the host as `lovable.dev/chats/…`; v03/v05/v06 read Claude chrome + `?artifact=project%3A…` with the *same* uuids — same project, one host read is wrong. Check claude.ai first, then lovable.dev.) Recovering it gives real CSS, real hex values, and the full-resolution portrait, and makes §2 of this spec obsolete. Ask him for it — it is a 2-minute ask that saves a day of colour-matching against a moiré-ridden phone video.

---

## 1. Two drafts exist. The still wins.

| | v01–v06 (clips) | image01 (still) |
|---|---|---|
| Shell | No sidebar. Sticky top bar: serif wordmark left, hamburger right | **Fixed cream left sidebar** with avatar, name, affiliation, 8+ nav items |
| Page bg | One flat warm ivory edge to edge | **Two-tone:** warm cream sidebar vs cool near-white content |
| Accent | brick red (v01, v05), royal blue (v02), none (v03, v04) | **brick red** active bar + **navy** content H1 |

The clips show the *content and component* work; the still shows the *shell* he actually approved. His one explicit instruction — *"sol kısımda menü olacak hep"* — is satisfied only by the still. **Build the still's shell; port the clips' components into it.** Everything the clips show about a top bar applies only to the <1024px drawer state.

Corroborating: his own Word source (v07, the Machine Learning guide) uses terracotta/brick-red section headings, blush callouts with an oxblood left rule, peach table headers. The site palette and the content he is pasting in must be continuous. That is strong independent evidence that **brick red, not blue, is the accent.**

---

## 2. Disputed readings — rulings

Ordered by build impact. "F" = first pass, "C" = critic.

1. **Diagonal background gradient (v02).** F: `linear-gradient(135deg,#F7F2E8,#F2E7D9)`. C: warmth is locked to *screen* position, not document position — identical spatial pattern at scroll 0 and scroll 100%, peaks at screen centre-top, falls off toward every edge. **Ruling: capture artefact. Flat background.** This was the single most load-bearing wrong claim in the whole set.
2. **Paper/linen texture (v01, v03).** F: faint vertical striation, possible linen. C: the striation drifts between frames, changes orientation, and runs over the *browser chrome* too. **Ruling: moiré. Flat fill. No noise overlay.**
3. **All display type sizes.** Every first pass inflated headings ~25–30% (photo px read as CSS px). C measured cap heights within single frames. **Ruling: use ratios.** H1 ≈ 2.0–2.2× body (not 2.7×); H2 ≈ 1.35–1.5× body; sidebar wordmark ≈ body size, *semibold*, not smaller/regular.
4. **Corner radii (v01).** F: photo 10–12px, button 8px. C: edge-tracing shows ≤2px on the button, 3–5px on the photo; blur can only *exaggerate* an arc. **Ruling: near-square. 4px photo, 2px button.** The design's character is hard-edged and print-like.
5. **Content column centring (v05).** F: centred, 72px gutters. C: flush left, ~220px of dead ivory on the right, right-aligned elements all stop at 78.6% — a `max-w-5xl` missing its `mx-auto`. **Ruling: C is right about what's on screen; it is a bug. Centre it** (flagged as a deliberate deviation, §9).
6. **Timeline rail (v01).** F: one continuous 1px spine with dots sitting on it. C: rail is *segmented per entry*, starts ~4px **below** each ring with clear background between, stops before the next entry; ring is 13–14px, not 8–9px; ring and rail are different colours. **Ruling: C.** Build as `border-left` on each `<li>` with the dot rendered separately above it.
7. **Short rule under section headings (v03).** F: 120–140px accent rule under "Research areas", called "the section-heading treatment". Both critics independently: clean space under every heading; the rule is the grid's *top border*, full measure, 55–65px lower. **Ruling: no heading underline exists. Do not build one.**
8. **Research-areas 2×2 grid (v03 vs v05) — UNRESOLVED.** v03's critic proved four hairline-*bordered* boxes (horizontal rules break across the gutter; two parallel verticals 18px apart; verticals vanish in the row gap). v05's critic proved no dividers at all (the "rule" lands at a different normalised position in every frame → moiré). Same page, two renders. **Ruling: build bordered cells** — v02's three homepage cards are confirmed bordered on all four sides by two independent critics, so bordered boxes are demonstrably in the design language. Cost of being wrong is one line of CSS. Verify against the recovered source.
9. **Hamburger chrome (v03 vs v06).** v03 C: rounded-rect box with 1px border, present in every frame. v06 C: the "border" sits at x=1597 in one frame and x=1577 in another — it moves, so it is moiré; bare bars only. **Ruling: borderless icon button** (a bordered box would be the only boxed element on a page with no boxes), 44×44 hit area.
10. **v04's "floating fixed byline".** F: two bare fixed text elements on transparent ivory, content scrolls under them — "arguably a bug". C: an H2 that should be visible at y≈68 is *completely absent* after an 85px scroll; only a descender pokes out below the occluding edge. **Ruling: an opaque fixed masthead band with a full-bleed 1px bottom border.** Not transparent.
11. **Footer.** v02's C proved the scrollbar reaches 100% → the homepage genuinely has **no footer**. v01's two critics contradict each other on whether the bottom was reached. **Ruling: there is no approved footer. Design one (§9).**
12. **Accent hue.** v06's C measured the contact icons as rose/crimson (B≈G) rather than terracotta. v07 (his Word doc) and image01's active bar are unambiguously brick (R−G = +63 on the active bar). **Ruling: brick/terracotta is the accent;** v06's rose reading is a lighter tint of the same family, given as `--brick-tint`.
13. **Elsewhere link icons (v06).** F: terracotta chain-links, "the only saturated colour". C: R−G = +4 on the link glyphs vs +14 on the contact glyphs, statistically identical to their own label text. **Ruling: the pending-link row is fully monochrome.** Accent appears only on the *filled* contact rows.
14. **Secondary button fill (v02).** One C: monotonic horizontal scan, no step at either edge → no panel, it is the illumination ramp. Other C: readable rectangular edge in four frames. **Ruling: ghost/text button at rest** (a monotonic scan is the stronger test), with an invented hover fill.
15. **Headshot aspect (v02).** F: portrait, slightly taller than wide. Both critics: 1.03–1.10 **landscape**. **Ruling: square to slightly landscape.** (v01's portrait is a separate, more landscape crop at 1.087:1.)
16. **Sticky header opacity.** All three critics who tested it proved **opaque** — content hard-clips at the border with zero bleed-through, no `backdrop-filter`, no scroll shadow, no background change on scroll. Unanimous; build it that way.
17. **Running head on every page (v07).** F: repeated per page. C: every continuation page top is clean whitespace. **Ruling: title-page masthead only.** Irrelevant on web except: don't invent a repeating page eyebrow.
18. **Callouts/tables at full measure (v07).** F: full text width. C: callouts are right-inset ~0.5in, tables inset both sides ~0.2in. **Ruling: C** — but on web, normalise: callouts and tables at full prose measure (§6.16, §6.17), since the inset is a Word artefact of single-cell-table construction.

---

## 3. Colour tokens

Every observed value is a phone camera on a ViewSonic panel: warm-shifted, exposure-ramped, moiré'd, with no neutral reference in frame. **Corrected = best guess after white-balancing on the brightest 1% of the page region.** The *relationships* are reliable and were verified at 17 separate heights in image01; the hexes are reconstructions.

| Token | Observed (raw) | **Corrected / use** | Role |
|---|---|---|---|
| `--paper` | `#B2AAA0` (under-exposed) | **`#FBFAF7`** | Content background. Cool near-white. |
| `--sand` | `#E4D3B2` | **`#F5EFE0`** | Sidebar, warm surfaces. The signature colour. |
| `--sand-2` | 6% darker than sand | **`#EDE5D0`** | Active nav row, table body cells, icon tiles. |
| `--blush` | `#FBEBE8` | **`#FBEDE9`** | Callout fill (from the Word source). |
| `--peach` | `#F7DACF` | **`#F6DACE`** | Table header fill, figure node fill. |
| `--rule` | `#DED7C8` | **`#E4DCCB`** | Hairlines on `--sand`. |
| `--rule-cool` | — | **`#E7E4DE`** | Hairlines on `--paper`. |
| `--oxblood` | `#8C2B2B` | **`#8C2B2B`** | Callout left bar, TOC rules. |
| `--ink` | `#151D12` | **`#1B2430`** | Sidebar name, strongest text. Cool-leaning. |
| `--navy` | `#122536` | **`#1B3A5C`** | Content H1/H2, links. Visibly **bluer** than `--ink` — two colours, not one. |
| `--text` | — | **`#3C4149`** | Body copy on `--paper`. |
| `--text-warm` | `#5E5943` | **`#52504A`** | Nav labels and body on `--sand`. |
| `--muted` | `#787167` | **`#6F6A61`** | Captions, meta, placeholders, pending links. |
| `--brick` | `(159,96,87)` | **`#A8443C`** | Accent: active bar, stat numerals, timeline dates/dots, figure emphasis. |
| `--brick-soft` | — | **`#B5564A`** | Hover/secondary accent. |
| `--brick-tint` | — | **`#F3E0DA`** | Accent wash (hover fills, badge backgrounds). |

```css
:root{
  --paper:#FBFAF7; --sand:#F5EFE0; --sand-2:#EDE5D0;
  --blush:#FBEDE9; --peach:#F6DACE; --brick-tint:#F3E0DA;
  --rule:#E4DCCB; --rule-cool:#E7E4DE; --oxblood:#8C2B2B;
  --ink:#1B2430; --navy:#1B3A5C; --text:#3C4149; --text-warm:#52504A; --muted:#6F6A61;
  --brick:#A8443C; --brick-soft:#B5564A;
}
```

**Rules that matter more than the hexes**

- The sidebar is **warmer and lighter** than the content — measured at 1.24 R / 1.22 G / 1.10 B at every height sampled. That stable two-tone contrast *is* what he means by *"renkler dizayn"*.
- **There is no border, divider, or shadow between sidebar and content.** The colour step is the separation. Do not add a `border-right`.
- The accent almost certainly comes from the **red brick wall behind him in the portrait**. If you need another warm tone, sample it from the photo rather than inventing one.
- **Zero shadows anywhere.** No elevation on the sidebar, no shadow under the avatar, no shadow on the active band, none on cards, none under the sticky header at any scroll position (three critics tested and confirmed).
- **One saturated accent, used sparingly.** In v01 the brick red appears only on stat numerals, timeline date ranges and timeline dots. Nothing else on the page is coloured. Keep that restraint.
- **Do not port the two blues from the clips:** v01's slate CV button (`~#88909F`) and v02's royal blue primary (`~#2E68A1`) are the only cool elements on otherwise entirely warm pages, and they contradict each other. Use `--navy` for interactive fills instead (§9, decision 3).

---

## 4. Typography

**Two families, strict role split.** Serif for the wordmark and every heading; sans for everything else. Zero exceptions anywhere in 8 clips — no bold serif, no uppercase, no letterspaced labels, no small caps. This split is what makes it read academic rather than startup.

### Serif (display)

The single most rigorous measurement in the set (v04 critic): x-height/cap ≈ **0.66–0.67**. That is an **old-style ratio** and positively rules out Lora (0.739), Libre Baskerville (0.754), Merriweather (0.774), Noto Serif (0.75) and Playfair Display (0.739) — all of which earlier passes guessed. It matches EB Garamond (0.666), Crimson Pro (0.652), Times (0.677).

- **Closest match:** an old-style / transitional in the Garamond–Crimson class.
- **Recommended, self-hostable:** **Crimson Pro** (variable, `@fontsource-variable/crimson-pro`, OFL). Alternate: **EB Garamond**.
- **Fallback if it reads too fine at 15–16px on screen:** **Source Serif 4** — slightly larger x-height, more robust at small sizes, same warm-academic register. Decide by eyeballing the sidebar wordmark, which is the smallest serif on the site.
- Weights: 400 for H1/H2/H3, **600 for the sidebar wordmark only** (v01 critic measured stem/cap 0.22 on the wordmark vs 0.146 on the H1 — the small mark is the *bolder* of the two, which both first passes got backwards).
- Stack: `"Crimson Pro Variable", "Crimson Pro", Georgia, "Times New Roman", serif`

### Sans (text / UI)

Every clip: double-storey `a`, single-storey `g`, straight-tailed `y`, open apertures, `G` with a straight spur, tall x-height.

- **Closest match:** Inter.
- **Recommended, self-hostable:** **Inter** (`@fontsource-variable/inter`, OFL). Ship weights 400/500/600 only; nothing needs 700.
- Stack: `"Inter Variable", Inter, system-ui, -apple-system, "Segoe UI", sans-serif`
- Enable `font-feature-settings:"cv05","ss01"` if you want the single-storey `g`; the mockup's `g` is single-storey but at this resolution it is not decisive.

### Scale (root 16px)

Ratios are from the frames; absolute values are chosen for screen legibility.

| Token | px / rem | Family | Weight | LH | Use |
|---|---|---|---|---|---|
| `--fs-h1` | 36 / 2.25 | serif | 400 | 1.18 | Page title (= 2.0× body ✓) |
| `--fs-stat` | 36 / 2.25 | serif | 400 | 1.0 | Stat numerals (≈ H1 size — deliberate, keeps the band academic not dashboard) |
| `--fs-name` | 28 / 1.75 | serif | **600** | 1.25 | Sidebar wordmark (= 1.7× nav ✓) |
| `--fs-h2` | 24 / 1.5 | serif | 400 | 1.25 | Section heading (= 1.35× body ✓) |
| `--fs-lead` | 20 / 1.25 | sans | 400 | 1.55 | Lead paragraph — **muted colour, same size family as body**, not a giant intro (v05 critic: lead line pitch is within 5% of body) |
| `--fs-h3` | 19 / 1.1875 | serif | 400 | 1.3 | Card / grid-cell titles |
| `--fs-body` | 18 / 1.125 | sans | 400 | **1.62** | Body copy (measured 1.625, not the 1.70–1.75 first passes claimed) |
| `--fs-nav` | 16 / 1 | sans | 400 | 1.4 | Sidebar nav label |
| `--fs-sm` | 15 / 0.9375 | sans | 400 | 1.55 | Card body, table cells, grid-cell body (a real second body size — grid text measures ~0.9× prose) |
| `--fs-xs` | 13 / 0.8125 | sans | 400 | 1.5 | Affiliation, captions, meta, sub-lines |
| `--fs-2xs` | 11 / 0.6875 | sans | 400 | 1.4 | Nav sub-label, timeline date ranges (uppercase, `letter-spacing:.08em`) |

Only two places get letter-spacing: timeline date ranges (`.08em`, uppercase, brick) and the eyebrow if you keep one (`.12em`, uppercase, muted). Nothing else.

**Measure: cap prose at 68–72ch.** Every clip runs 89–110 characters per line (v04: 93–95 chars; v05: 95–100; v06: ~95). Three critics independently flagged it as a defect. Tell him you tightened it and why.

---

## 5. The shell

### 5.1 Sidebar

```css
:root{ --sidebar-w:300px; --gutter:20px; }
@media (max-width:1279px){ :root{ --sidebar-w:272px; } }

.sidebar{
  position:fixed; inset:0 auto 0 0;
  width:var(--sidebar-w); height:100dvh;
  display:flex; flex-direction:column;
  background:var(--sand);
  padding:40px 0 32px;
  border:0;                    /* no divider — the colour step is the separation */
  overflow:hidden;
}
.sidebar__head{ padding-inline:var(--gutter); flex:0 0 auto; }
.sidebar__nav { padding-block:0; flex:1 1 auto; overflow-y:auto; overscroll-behavior:contain; }
```

- **Width 300px** (measured 36.6% of it = the avatar; 5% of it = the gutter). 272px below 1280px.
- **`position:fixed`, full `100dvh`, own `overflow-y` on the nav only.** Evidence: in the still, the avatar is clipped by the viewport top while the content column is mid-scroll — the sidebar scrolls independently. Give it `padding-top:40px` so the avatar never clips the way it does in the draft.
- **One left gutter of 20px governs everything** — avatar, name, affiliation, every nav label, and the sub-label. The sub-label is **not indented** under its parent (verified: same left edge). That flatness is the layout's discipline.

**Head block, top to bottom:**

```
avatar (110px circle)  →24px→  name  →12px→  affiliation (3 lines)  →32px→  nav
```

```css
.sidebar__avatar{ width:110px; aspect-ratio:1; border-radius:50%;
  object-fit:cover; display:block; border:0; box-shadow:none; }
.sidebar__name{ font:600 var(--fs-name)/1.25 var(--serif); color:var(--ink);
  margin:24px 0 0; }
.sidebar__affil{ font:400 var(--fs-xs)/1.5 var(--sans); color:var(--muted);
  margin:12px 0 0; }
```

No ring, no border, no shadow, no plate behind the avatar. The photo bleeds to the circle edge.

### 5.2 Nav

**Order (the still, top to bottom — the only frame showing the real menu):**

| # | Label | Route | Sub-label |
|---|---|---|---|
| 1 | Home | `/` | |
| 2 | About Me | `/about` | |
| 3 | My Research Areas | `/research` | |
| 4 | Gallery | `/gallery` | |
| 5 | Vibrations and Waves | `/vibrations-waves` | |
| 6 | Signal Processing & Optimization | `/signal-processing` | System Identification · Estimation · Optimization |
| 7 | Machine Learning | `/machine-learning` | |
| 8 | Blog | `/blog` | |
| 9 | Contact | `/contact` | *(not visible — the still is scroll-truncated below "Blog"; `/contact` is proven to exist by v06)* |

Verbatim rules: **ampersand** in "Signal Processing & Optimization" (not "and"); **spelled "and"** in "Vibrations and Waves"; sub-label separators are **spaced middots ` · `**, not slashes or bullets. No icons, no bullets, no chevrons, no counts, no group headings, no dividers, no accordions — it is one flat list, the three research areas sit at the same level as Home and Blog.

```css
.nav a{
  display:block; position:relative;
  padding:11px var(--gutter);
  font:400 var(--fs-nav)/1.4 var(--sans);
  color:var(--text-warm); text-decoration:none;
}
.nav li + li{ margin-top:4px; }            /* 44px band + 4px gap ≈ 48px pitch */
.nav a:hover{ background:rgba(27,36,48,.035); }          /* INVENTED — no hover captured */
.nav a:focus-visible{ outline:2px solid var(--brick); outline-offset:-2px; }

/* Active = three cues at once */
.nav a[aria-current="page"]{
  background:var(--sand-2);                /* ~6% darker, same hue */
  color:var(--ink); font-weight:500;
  border-radius:0;                         /* square — NOT a pill, NOT inset */
}
.nav a[aria-current="page"]::before{
  content:""; position:absolute; left:0; top:0; bottom:0;
  width:3px; background:var(--brick);      /* per-item bar, NOT a continuous rail */
}
.nav__sub{
  display:block; margin-top:3px;
  font:400 var(--fs-2xs)/1.4 var(--sans); color:var(--muted);
}
.nav a[aria-current="page"] .nav__sub{ color:var(--muted); }  /* sub-label does not darken */
```

**Active state is a compound of three cues, all firing together:**
1. Full-bleed band spanning the **entire sidebar width, edge to edge, square corners, not inset from the gutter**.
2. **3px brick-red vertical bar flush to the sidebar's left edge**, exactly the same height as the band, top and bottom aligned. Verified present on the active item only — the same 3px column at three inactive rows is plain cream. **Do not build a continuous rail with a sliding indicator.**
3. **Darker, slightly heavier label** (measured: 5th-percentile ink 86 on "Home" vs 106 on "About Me" in the same exposure).

The one row carrying a sub-label **grows taller** (~+16px) rather than compressing its band.

### 5.3 Collapse breakpoint — the one thing every draft got wrong

Measured collapse widths in the drafts: **≥1110 CSS px (v06), ~1280 (v05), ~1350–1450 (v02)**. All of them show a hamburger at widths where a desktop sidebar should be up. That directly violates his only explicit instruction.

**Spec: the sidebar persists down to 1024px.** Below that it becomes an off-canvas drawer.

```css
@media (max-width:1023px){
  .sidebar{ transform:translateX(-100%); transition:transform 220ms ease;
            width:min(300px,84vw); z-index:60; }
  .sidebar[data-open]{ transform:none; }
  .topbar{ display:flex; }
  .content{ margin-left:0; padding:24px 20px 64px; }
}
@media (prefers-reduced-motion:reduce){ .sidebar{ transition:none; } }
```

**Top bar (<1024px only)** — this is where the clips' header findings apply:

- Height 64px, `position:sticky; top:0`, **fully opaque** `background:var(--paper)` (no `backdrop-filter`, no rgba — three critics proved content hard-clips at the border), `border-bottom:1px solid var(--rule-cool)`, **no shadow at any scroll position**, no background change on scroll.
- Serif wordmark "Korkut Kaynardag, PhD" left at 18px/600; hamburger right.
- **Hamburger:** borderless, no box, no radius. 3 equal-length bars, 2px thick, 6px gaps, 24×22 glyph, colour `--ink`, inside a 44×44 hit area. (v06's critic proved the "border" other passes saw moves between frames — it is moiré.) Note the drafts also put it slightly *above* the wordmark's optical centre; that is keystone plus a real ~10px offset — centre it properly.
- Drawer behaviour: overlay `rgba(27,36,48,.32)`, close on Esc / overlay click / route change, focus trap, `aria-expanded` on the button, body scroll lock. **None of this is in the mockup — it is invented and must be.**

### 5.4 Page shell

```css
.content{ margin-left:var(--sidebar-w); background:var(--paper); }
.container{ max-width:1080px; margin-inline:auto; padding:64px 48px 96px; }
.prose{ max-width:68ch; }
.wide{ max-width:100%; }     /* card grids, tables, figures */
```

- Content background `--paper`, sidebar `--sand`, **nothing between them**.
- Wide blocks (card grids, tables, the stat band) go to 1080px; prose caps at 68ch inside it.
- The drafts ran flush-left with ~20% dead space on the right. **Centre it** — §2.5, §9.1.

### 5.5 Vertical rhythm

```
h1                         → lead            20px
lead                       → first section   40px
section (h2 block) top margin              56px
h2                         → first paragraph 28px
p + p                                        18px   (0.6 of a line, not a full blank line)
hr                          margin          44px top / 56px bottom  (asymmetric, as measured)
figure                      margin-block    40px
figcaption                  margin-top      12px
list item + item                            12px
timeline entry + entry                      40px
```

Spacing scale to build from: `4 8 12 16 20 24 28 32 40 48 56 64 80 96`.

---

## 6. Components

Every one of these is observed in the frames. CSS is the corrected reading.

**6.1 Hairline divider.** `border:0; border-top:1px solid var(--rule-cool); ` at full **container** width, not prose width — the drafts consistently run rules ~15% wider than the text block (v06: rules still strong at x=1600 where prose ends at x=1289). One `<hr>` per page maximum; the drafts use exactly one, after the lead paragraph.

**6.2 Page header.** Serif H1 in `--navy`, immediately followed by a sans lead paragraph in `--muted`. **No eyebrow, no kicker, no subtitle, no byline, no date, no rule under the H1** — verified by threshold-scanning the band between the header and the H1 in three clips. (v02's homepage is the one exception: it has an uppercase letterspaced eyebrow `ACADEMIC & RESEARCH PORTFOLIO` at ~0.8× body, not the 0.7× first reported.)

**6.3 Prose paragraph.** `--fs-body` / 1.62 / `--text`. Bold run-ins (`<strong>Scope:</strong>`, `<strong>Real-world:</strong>`) open many paragraphs — in the Word source these are near-black bold, except inside one callout where they are brick red. **Normalise to near-black bold**; the source is inconsistent. No first-line indents; paragraphs separate by space only. No drop caps, no pull quotes.

**6.4 Stat band (v01, `/about`).** Three equal columns, full container width, `border-block:1px solid var(--rule-cool)`, faint 1px verticals between cells, band ~130px tall, each cell centre-aligned: **serif numeral in `--brick` at `--fs-stat`** over a `--fs-xs` `--muted` label. No cards, no fills, no borders around cells. Keeping those numerals *serif* is most of why the band reads academic instead of dashboard.

**6.5 Timeline entry (v01).** Per-entry `border-left:1px solid var(--rule)`, ring rendered **separately, above** the rail with ~4px of background between them. Ring 13px, 2px stroke in `--brick`, hollow centre. Text indented 26px from the dot centre. Stack: `--fs-2xs` uppercase letterspaced **brick** date range → `--fs-h3` serif `--ink` role → `--fs-sm` `--text` org+location → `--fs-sm` `--muted` description. **Two-level contrast step inside each entry — the org line is dark, the description muted.** No cards, no icons, no logos.

**6.6 Profile-link row.** Horizontal flex, **fixed `gap:42px`, content-sized items, left-aligned** — not `space-between`, not a 3-column grid (measured: gaps identical at 61–62px, item widths 383/321/386px). Each item: a Lucide `link-2` glyph (horizontal two-link chain, ~10px) + 8px + label. **All monochrome `--muted`, no underline, no accent, no link colour** — these are disabled placeholders and read at the same tonal tier as the `[… coming soon]` italics, one step lighter than body.

**6.7 Contact detail row.** 22px icon gutter + 45px gap + text stack. Outlined Lucide icons (`building`, `mail`, `map-pin`) at 1.75px stroke, in `--brick`. Label `--fs-sm` weight 600 in `--ink` (**not** body grey — measured with the headings, 25 units darker than the lead), sub-line `--fs-xs` `--muted`. Rows 28px apart. No card, no border, no fill, no hover.

**6.8 Placeholder convention.** `[Email address coming soon]` — **literal square brackets, italic sans, `--muted`**. Used consistently as the site's "not filled in yet" idiom. Keep it; when real values arrive, the brackets and the italic go with them.

**6.9 Topic card (v02 homepage grid).** Three equal columns, `gap:28px`, equal height.
```css
.card{ border:1px solid rgba(0,0,0,.05); background:rgba(255,255,255,.4);
       border-radius:3px; padding:30px; box-shadow:none; }
```
Border and fill are **very faint** — measured 4–5 levels on a base of 216, i.e. ~2%, roughly half what was first reported as `#E6DCCC`. Four discrete bordered boxes; borders do **not** cross the gutters. Contents: serif H3 → `--fs-sm` `--muted` body → `Read more →`. **`Read more →` is *not* bottom-pinned** — in the draft, card 1's sits 78px above its bottom border and card 2's 42px. Card 2 (with the two-line title) sets the row height. If you pin it, all three align and the draft's look changes. *Decide deliberately; pinning is the better design, so pin it and say so.*

**6.10 Research-areas 2×2 grid (`/research`).** Four cells, `gap:18px`, `border:1px solid var(--rule-cool)`, `padding:25px`, square corners, no fill, no shadow. Cell = serif H3 title (wraps to two lines) + `--fs-sm` `--muted` body at **1.5 line-height — tighter than prose**, which is a real second body style. See §2.8 for the dispute.

**6.11 Document / download row.** The site's one repeating interactive pattern; build it once, feed it a status flag.
```css
.doc{ display:flex; align-items:flex-start; gap:20px; padding:20px 24px; }
.doc__tile{ flex:0 0 44px; height:44px; border-radius:8px; background:var(--sand-2);
            display:grid; place-items:center; }   /* tile ~7% darker than page, not 4% */
.doc__body{ flex:1 1 auto; }
.doc__title{ font:500 var(--fs-body)/1.4 var(--sans); color:var(--ink); }
.doc__meta { font:400 var(--fs-xs)/1.5 var(--sans); color:var(--muted); }
.doc__desc { font:400 var(--fs-sm)/1.5 var(--sans); color:var(--text); }
.doc__dl   { margin-left:auto; align-self:flex-start;  /* baseline of the TITLE, not centred */
             font:400 var(--fs-xs) var(--sans); color:var(--muted); display:inline-flex; gap:8px; }
```
- **`align-items:flex-start`** — the Download action baselines with the *title's first line*, 17px above the row's vertical centre. The icon tile is top-aligned too.
- The row is **inset ~24px inside the prose column on both sides**, not full-bleed (v04 critic corrected this in three respects).
- **No divider under the row.** Both v04 critics independently disproved it with scans across three frames.
- Download glyph sits **left** of the word. `Download` is the **lightest text on the page** — the only call to action has the weakest contrast. **Fix this:** give it `--navy` and an underline on hover.
- All four doc icons in v05 are identical regardless of file type. Don't invent per-type icons without asking.

**6.12 CV button (v01).** Solid fill, 2px radius (not 8), 46px tall, full media-rail width, white 15px label + 16px download glyph. The draft fills it slate blue-grey — the only cool element on an entirely warm page. **Recommend `--navy` fill** for consistency with the content H1 (§9.3).

**6.13 Portrait figure.** `border-radius:4px` (measured 3–5px, not 10–12), no border, no shadow, aspect 1.09:1 on `/about`, ~1:1 on the homepage hero. Homepage hero image is **vertically centred on the whole hero row** (`align-items:center`, matched to 2.5px), not top-aligned. Image column is **~26% of content width**, text ~69%, gap ~4%.

**6.14 Figure + caption.** Figure centred, up to prose width. Caption: **italic, `--muted`, centred, at full prose measure** (not constrained to the figure's width), `--fs-xs`. `Figure N.` is **not bold** — it is uniformly italic with no weight change at the run-in (three frames confirm).

**6.15 Ordered list (v02).** Numerals hang left of the list text but sit **~10px right of the prose margin** — they do not hang outside the content column. Wrapped lines align to the text, not the numeral.

**6.16 Callout / aside** (needed for the ported Word content — v07 uses it 5+ times).
```css
.callout{ background:var(--blush); border-left:4px solid var(--oxblood);
          border-radius:0; padding:20px 24px; margin-block:32px; }
.callout > h4{ font:600 var(--fs-sm) var(--sans); color:var(--brick); margin:0 0 12px; }
.callout p:last-child{ font-weight:600; }   /* these callouts end on a bold takeaway */
```
The source has two inconsistent variants (heavy left bar vs a thin four-sided outline) and they are Word single-cell tables. **Normalise to the left-bar variant** — it appears more often and is the stronger pattern.

**6.17 Table.** Header fill `--peach`, header labels brick-red 600, body cells `--sand-2` at 40% or plain, `border:1px solid var(--rule)` on every cell, square corners, narrow first label column. **The source is internally inconsistent** (one table has an unfilled header over filled body, another the reverse; one fills per *column* not per row). **Pick the filled-header convention and apply it everywhere.** Cell text left-aligned, ragged right — the source's justified narrow cells produce rivers several ems wide and are the worst artefact in the document. On <768px, collapse to stacked blocks per row; do not horizontal-scroll.

**6.18 Per-model content template (v07, Section 4).** Prose paragraph → three bullets with bold run-ins `Real-world:` / `Use it when:` / `Think twice when:` → figure. Repeated for every model in the ML guide. Build it as one component and drive it from frontmatter; it is the most reusable structure in his content.

**6.19 In-page TOC.** The Word doc's 12-entry numbered TOC with dotted leaders and maroon rules becomes the page's section nav on web. Render as a sticky right-hand TOC on ≥1440px, or an inline collapsible block above the first section below that. Every `Section 5.3` / `Figure 7` cross-reference in his prose becomes an anchor link — **this is the single biggest thing a website gives him over the .docx** and is worth saying to him explicitly.

**Not present anywhere in 8 clips, and must not be introduced:** shadows, elevation, gradients, rounded cards, pills, badges, tags, chips, callout boxes in the *site* chrome, tabs, accordions, breadcrumbs, back-to-top, dark-mode toggle, search box, social icons, avatars in content, hero overlays, or any decorative texture. Structure is carried entirely by hairlines and whitespace. Any rebuild that adds card shadows breaks the approved look.

---

## 7. Motion

**Zero motion is observed in any of the eight clips.** Quantified: mean absolute luma difference between two frames at the same scroll position is 4.1–5.2 (pure camera micro-motion, no region changes independently); identical glyph ink density at every scroll position rules out fade-in-on-scroll; the sticky header never gains a shadow, border, or background change. The cursor never lands on a link, button, card, or the hamburger in any frame — **no hover, focus, active, or transition state exists in the approved design.**

Everything below is therefore an invention, not a restoration. Keep it minimal:

- Nav hover / active: `transition: background-color 140ms ease, color 140ms ease`
- Drawer: `transform 220ms cubic-bezier(.32,.72,0,1)`; overlay `opacity 180ms`
- Links: colour + `text-decoration-color` on hover only
- Nothing else. No scroll reveals, no parallax, no page transitions, no animation library.
- Wrap all of it in `@media (prefers-reduced-motion:reduce){ *{animation:none!important;transition:none!important} }`

---

## 8. Astro implementation notes

```
src/
  layouts/BaseLayout.astro        # <html>, fonts, tokens, skip-link, Sidebar + <slot/>
  layouts/ArticleLayout.astro     # long educational sections: TOC, figure numbering, PDF link
  components/Sidebar.astro
  components/MobileBar.astro      # <1024 top bar + hamburger + drawer controller
  components/DocRow.astro
  components/StatBand.astro
  components/TimelineEntry.astro
  components/TopicCard.astro
  components/Callout.astro
  components/Figure.astro
  data/nav.ts                     # single source for nav order + sub-labels + routes
  styles/tokens.css               # the :root block from §3
  styles/base.css                 # reset, type scale, prose
  pages/…                         # index, about, research, gallery, blog/[slug],
                                  # vibrations-waves, signal-processing, machine-learning, contact
content/                          # existing collections — keep as-is
```

- **Nav in one file** (`src/data/nav.ts`), consumed by both the sidebar and the drawer. Active via `aria-current="page"` derived from `Astro.url.pathname` (handles `/blog/*` → Blog as active parent).
- **Fonts:** `@fontsource-variable/crimson-pro` + `@fontsource-variable/inter`, self-hosted, `font-display:swap`, preload the two woff2 files. No Google Fonts request (Cloudflare Pages, and it is faster).
- **Portrait:** `astro:assets` `<Image>`, served at 2× (220px), `loading="eager"`, `fetchpriority="high"`. Extract the full-res original from the recovered project or from `reference/wix-media/`, not from video frames.
- **KaTeX** per the existing decision — `remark-math` + `rehype-katex`, CSS self-hosted.
- **`docx2page.py` output** should emit the component vocabulary above: `.callout`, `.doc`, `<figure>`/`<figcaption>`, and anchor-linked `Section N.M` / `Figure N` cross-references.
- Accessibility floor: skip link, `<nav aria-label="Main">`, visible `:focus-visible` on every interactive element, 44px minimum hit targets, `--muted` on `--paper` is 4.6:1 (passes AA for body but **fails for the 11px sub-label** — bump the sub-label to `--text-warm` or 12px).

---

## 9. Not specified by the mockup — decisions needed

Ranked by how much they block the build.

1. **Content column centred or flush-left.** The draft is flush-left with ~20% dead space on the right — almost certainly a missing `mx-auto`. **Recommend centring.** Show him both; it is a one-line change.
2. **Footer.** Proven to not exist on the homepage. He needs one: contact, ORCID/Scholar/LinkedIn, copyright, "last updated". **Recommend** a `--sand`-tinted band inside the content column with a top hairline, three columns collapsing to one below 768px.
3. **Interactive colour.** Two mutually contradictory blues in the drafts (slate `#88909F` CV button, royal `#2E68A1` primary). **Recommend** `--navy` `#1B3A5C` for all fills and links, `--brick` reserved for accents only.
4. **`Read more →` bottom-pinned or not.** Draft: not pinned, so the three cards' links misalign. **Recommend pinning.**
5. **Hover / focus / active states for everything.** Nothing is captured. All invented (§7).
6. **Mobile breakpoint confirmation.** Every draft collapsed the menu at 1110–1450px, contradicting his instruction. **Recommend 1024px** — confirm with him, since this is his one stated requirement.
7. **Turkish diacritics.** The drafts render `Kaynardag`, `Izmir`, `Istanbul`, `Turkey` in plain ASCII. PROJECT.md §5 already records the decision to keep **both spellings** (`Kaynardağ` and `Kaynardag`) for Google Scholar indexing — apply that deliberately: `Kaynardağ` in visible headings and `<title>`, `Kaynardag` in a `<meta name="author">` alt-spelling and schema.org `alternateName`. Fix `İzmir`, `İstanbul`, and decide `Turkey` vs `Türkiye`.
8. **Dark mode.** Not specified anywhere. Light-only for v1; the token structure supports adding it later.
9. **Gallery layout.** 27 photos, 14 sets. No gallery frame exists in any clip. Needs its own design pass.
10. **Which email is public.** `korkut.kaynardag@gmail.com` appears in the Word doc's disclaimer; `korkutkaynardag@iyte.edu.tr` is institutional. Ask before publishing either.
11. **Sub-label asymmetry.** Only "Signal Processing & Optimization" has one; "Vibrations and Waves" and "Machine Learning" do not (verified at lowered threshold — nothing faint is hiding there). Almost certainly unfinished. Either give all three one or none.
12. **Source-content inconsistencies to confirm, not silently fix:** `Sound Source Tracking` vs `Sound Wave Tracking` (same topic, two names, one page); `Figure 11` in body vs `Figure 13` in the caption; `multi-layer perception` (should be *perceptron*); `and the any setting`; `nondestructive` vs `non-destructive` on the same page; `PhD` vs `Ph.D.`; unspaced en-dash `(2023–2024)` in prose vs spaced em-dash `2026 — PRESENT` in the timeline; Oxford comma present in the bio but absent in the timeline's version of the same list. Batch them into one message to him.
13. **`At a glance — September 2026`** hard-codes 12 articles / 2 patents / 8 awards with no update mechanism. Drive it from a data file and add a "last updated" line.
14. **Gallery route referenced but unbuilt.** His `/research` copy says "You'll also find these documents under the Gallery section" — the route must exist and actually hold those documents, or the sentence has to change.
15. **The three research-area pages are shells.** `/vibrations-waves` has a finished H1, lead, four H2s and a Documents card, and every section body is a literal `[Content coming soon — …]`. The bracketed text is a useful spec of what goes there; keep it as authoring notes rather than deleting it. This is the paste-in template for all three topic pages: byline → H1 → lead → N serif H2 sections → Documents section with file rows, at `/<topic-kebab-case>`.