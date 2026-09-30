# Integration to-do (build.py owner applies after workflow B finishes)

Status, 2026-09-23 integration: every item below is resolved in the shipped build. The arrow,
the two copy fixes, the Gallery titles, the About gap, the separate timeline and the figure
breakout are in; the fallback hero lost its eyebrow line; `--strict` passes with 0 em dashes.

Collected from the reviewers' integrator notes. Workflow B owns build.py until it reports;
do not edit build.py before then.

## From workflow A (about, gallery) — 2026-09-23

1. **Arrow in build.py** (`ARROW`, the "Start here" row on the three topic pages and the
   gallery fallback): still 18px, stroke-width 1.5, rest dashoffset 9. The head travels 3.75px,
   not the brief's 5px, rests looking like a typed "->", and is not gated for reduced motion.
   Match rboxes.py and gallery.py: width/height 24, stroke-width 1.25, rest offset 5, travel only
   under `(prefers-reduced-motion:no-preference)`.
2. **"Twelve chapters"** in the ML guide's DOCS lede: his guide says "Section" 67 times and
   "chapter" never. Use "sections".
3. **"behaviour"** in DOCS: his title spells it "Behavior". Use his spelling.
4. Gallery labels and the doc-page `<h1>` differ for three documents (see parts/gallery.md).
   Pick one source of truth.
5. About page: add `.about > div > :last-child{margin-bottom:0}` (or equivalent). At 1001px and
   wider the gap above "At a glance" is 68.85px against 21px below it, 3.28:1, over the brief's
   2.5:1 cap; 21.85px of it is a paragraph margin trapped in the .hero grid cell.
6. The timeline spine in about.py needs at least 240px of page below its last node, or the last
   node never inks at max scroll. Watch the footer margin.
7. If a separate parts/timeline.py ships, strip the `.tline` block (CSS and the timeline half of
   the JS) from about.py; it becomes dead weight. Keep the accessible source order in any
   timeline: the role's `<h3>` first, its dates after it, dates drawn first with CSS only.

## From round 2 (site/candidates/r2) — worth checking against the new work

8. The r2 shell reviewer found that **16 of the 101 figures sit inside table cells** (12 in td,
   4 in th). A figure breakout rule written for `.doc figure` also hits those and produced a 4x
   horizontal scroll. Check whatever parts/docs.py ships for the same trap:
   the breakout must target only top-level figures in the document flow.
9. Playwright WebKit on Windows does not paint scroll-driven animation state and renders
   variable-font 600 as 400. Verify WebKit by computed values, not screenshots.

## Standing

10. The only em dashes left on navigation pages are 2 in parts/hero.py (index.html); workflow C1's
    hero designer owns that file. `python site/build.py --strict` must pass before publishing.
11. Rename parts/timeline_final.py to parts/timeline.py once workflow C1's judge and verifier
    are done.
