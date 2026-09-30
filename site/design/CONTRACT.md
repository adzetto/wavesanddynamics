# Design contract — wavesanddata.com

You are building one section of a real, live academic site for **Korkut Kaynardag, PhD**
(Assistant Professor, Civil Engineering, Izmir Institute of Technology). It is already
published on Wix as a static site. Treat it as production, not a demo.

**There is no "preview" framing anywhere.** No notes about how the site was built, no
"onizleme", no mention of converters, PowerPoint, Lovable, Ricos or measurements. A
visitor must see only the professor's own site.

The site's subject: structural health monitoring (SHM), non-destructive testing (NDT),
wave propagation and dynamics, acoustic wave-based sound source tracking, signal
processing, system identification, estimation, optimization, and machine learning for all
of the above. Applied to tall buildings, masonry buildings and bridges, a suspension
bridge, wind turbines, railway tracks and vehicles.

---

## 1. Palette — fixed, do not invent colours

Measured out of the professor's own deck. Use the CSS variables, never raw hex.

```
--page      #FFFFFF   page background — white, always
--surface   #FAFAFA   faintly raised band
--card      #F2F2F2   card fill
--line      #D1D1D1   card border
--rule      #E9E9E9   hairline separator
--nav       #104862   deep teal — the sidebar, primary actions
--nav-2     #0C3A50   its pressed/hover shade
--accent    #80350E   rust — the single accent: active state, numerals, small marks
--accent-2  #A0522F   lighter rust, for gradients/hover only
--wash      #F6F1ED   faint rust wash
--ink       #14202B   headings
--body      #3F4650   body copy
--muted     #6E7681   captions, secondary
--link      #104862
```

Exactly two saturated colours exist: `--nav` teal and `--accent` rust. Nothing else.
Never add a third hue. Gradients, if any, stay inside one hue.

Dark mode: the page already redefines every token under
`@media (prefers-color-scheme: dark)` and `[data-theme="dark"]`. Use the variables and
dark mode works for free. **Never hardcode a colour that must flip.**

## 2. Scale, radius, motion

```
--r-sm 10px   --r-md 14px   --r-lg 20px   --r-pill 999px
--sh-1 0 1px 2px rgba(20,32,43,.05)
--sh-2 0 2px 4px rgba(20,32,43,.04), 0 10px 28px rgba(20,32,43,.07)
--sh-3 0 3px 6px rgba(20,32,43,.05), 0 18px 44px rgba(20,32,43,.10)
--ease cubic-bezier(.2,.8,.2,1)     /* Apple's standard out-curve */
--ease-in-out cubic-bezier(.4,0,.2,1)
--t-fast 160ms   --t-mid 240ms   --t-slow 420ms
```

Spacing: multiples of 4 — 4 8 12 16 20 24 32 40 48 64 80 96.
Type: 12 / 13 / 14 / 15 / 16.5 / 18 / 21 / 25 / 32 / 40 px.
Fonts, already loaded: `Inter` (UI and body), `"Source Serif 4", Georgia, serif`
(headings only). No other family, no icon font.

## 3. Apple HIG rules that bind you

- **Deference.** Content leads; chrome recedes. No decoration that carries no meaning.
- **Clarity.** Generous negative space. One idea per block. Never crowd.
- **Depth.** Layer with subtle elevation and translucency, never heavy drop shadows or
  borders that shout. Prefer a hairline + a whisper of shadow over a thick outline.
- **Motion is feedback, not decoration.** It tells you something changed or where
  something came from. 160–420 ms. Never loops, never bounces for its own sake,
  never animates on page load in a way that delays reading.
- **Hit targets ≥ 44 × 44 px.** Whole cards are targets, not just their labels.
- **Contrast ≥ 4.5:1** for body text, ≥ 3:1 for large text and meaningful graphics.
- **Alignment is structure.** Everything lands on the same left edge or the same grid.
- **Every interactive element needs a visible `:focus-visible` ring** — 2px `--nav`,
  2px offset. Keyboard users see exactly what mouse users see.
- Respect `@media (prefers-reduced-motion: reduce)` — kill transforms and transitions,
  keep the end state. Non-negotiable.

## 4. Technical constraints — hard

- Output is a **static file on Wix**: 3 MB per file, 20 MB per site. Be frugal.
- **Inline SVG only** for icons — no raster, no icon font, no sprite file, no external
  request. Each icon ≤ 800 bytes of markup, `viewBox="0 0 24 24"`, `stroke="currentColor"`,
  `fill="none"`, `stroke-width="1.5"`, `stroke-linecap="round"`, `stroke-linejoin="round"`.
  They must read as one family: same weight, same corner radius, same optical size.
  Mark them `aria-hidden="true"` when a text label sits beside them.
- **No JavaScript framework.** Prefer pure CSS. If a behaviour genuinely needs JS, write
  ≤ 40 lines of vanilla JS, feature-detect, and make the section fully usable and
  fully legible **without** it. `IntersectionObserver` for reveal-on-scroll is allowed;
  a reveal must never leave content invisible if the observer never fires.
- No `<style>` or `<script>` inside your HTML fragment — CSS goes in your `.css` file,
  JS (if any) in a `JS` string your module exports.
- Semantic HTML. Headings in order. Lists are lists. Links are `<a>`, buttons `<button>`.
- Must work from 320 px to 2560 px wide. The site has a fixed 264 px left sidebar above
  1000 px; below that the sidebar becomes a drawer and your section is full width.
  Your content area is therefore roughly `min(1020px, 100vw - 264px) - 96px` on desktop.

## 5. What you deliver

Exactly two files, both under `parts/`:

**`parts/<name>.py`** — one module, no side effects on import:

```python
CSS = """ ... your scoped CSS ... """
JS  = """ ... optional, '' if none ... """

def render(**kw):
    """Return the section's HTML as a string."""
```

The builder concatenates every `CSS` into one stylesheet and every `JS` into one script,
then calls `render()`. So:

- **Scope every selector** under one root class you own (e.g. `.topics`, `.rboxes`).
  A bare `h2 { }` or `.card { }` would leak into other sections and break them.
  The only exception is a `@keyframes` name, which you prefix with your section name.
- Do not redefine any `:root` variable. Read them, never write them.
- Your `render()` takes only the keyword arguments named in your brief.
- Write real content, never lorem ipsum, never a TODO.

**`parts/<name>.md`** — 10 lines max: what you built, the interaction, and anything the
integrator must know (a variable you expect, a JS hook, a caveat).

## 6. How you will be judged

1. Does it look like it belongs on a serious researcher's site — restrained, confident,
   expensive? Or does it look like a template?
2. Would this pass an Apple design review: deference, clarity, depth, purposeful motion?
3. Does it degrade perfectly — no JS, reduced motion, keyboard only, 320 px, dark mode?
4. Is the CSS scoped, small, and free of magic numbers that fight the scale above?
5. Is the copy the professor's own subject matter, accurate and free of filler?

Build it as though it ships tonight. Because it does.
