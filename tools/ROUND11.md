# Round 11 (27 Sep 2026): the brief every agent reads first

Read `tools/ROUND10.md` first. Its sections "Load these skills before you design", "The
site's rules" and "How to work alongside each other" bind this round unchanged, with
these differences:

- Build to `build/r11-<you>/dist`, not r10. Use a port from 8971 to 8999; the
  controller uses 8960.
- The client's feedback this round came from the professor himself.

## The professor's rule for every page (new, binding)

He wrote, in Turkish: "karsidaki kisiyi en kisa zamanda, aklini karistirmicak sekilde,
sundugun bir seyi anlamasini saglamak". In English: whatever a page presents, the reader
must understand it in the shortest time, without being confused.

He judged the Big Picture's document shelf "karmasik olmus" (it got complicated). What
this means for your work:

- Make the thing the reader must grasp first the most visible thing.
- Group each item under what it belongs to.
- Show one idea per visual.
- Never list the same thing twice.
- Motion must clarify; it must never decorate.

When taste and clarity disagree, clarity wins.

## The figure palette changed (orange is gone)

The client disliked the burnt orange in the figures. Figures now use the site's inks and
blues, plus one crimson. `tools/numfig/engine.js` is the source.

- **Accent** (the thing the eye follows): `#A7203A`.
  It has the same CIELAB lightness as the blue `#095A94`.
- **Amber** (the brighter second warm, used for flashes, second series and edges):
  `#D14457`.
- **Wash** (a light tint behind a highlight): `#F9EEEE`.
- **Deep** (dark strokes and shadows): `#781E2C`.
- **Diverging map, from negative to positive:** `#043052 #2E6A9E #9CBBD6 #FFFFFF #DEABAB
  #B03F4D #651020`.

Orange remains in one place only: machine learning Figure 14 (kNN). Its caption, which is
his text, names the classes "orange" and "purple". Wherever his words name a colour, the
figure keeps that colour.

The site UI's own `--accent` token is unchanged this round. Do not change `theme.py`.

## Who owns what this round (only touch your own files)

- **bp**: `site/parts/documents.py`, `tests/test_bigpicture.py`, `tools/bp_art.py`,
  `content/bigpicture/`.
- **blog**: `site/parts/blog.py`, `tests/test_blog_index.py`.
- **contact**: `site/parts/contact.py`, `tests/test_contact.py`.
- **deck**:
  - `tools/deck/`, `content/deck-probstat/`, `site/parts/deck.py`, `tests/test_deck.py`
    and `tests/test_deck_system.py`;
  - in `site/build.py`, only the block that starts with the comment "His decks, a slide
    viewer each".
- **shm**:
  - new generators `tools/numfig/shm_*.py`;
  - `content/anim/nf-shm-*`;
  - the three SHM and brochure entries in `content/anim/anim.json`, or a new
    `content/anim/anim.shm.json` fragment;
  - `content/anim-originals/`;
  - a new `tests/test_shm_figures.py`.
- **controller**: `tools/numfig/engine.js`, `common.py` and every other generator, all
  other `content/anim/nf-*` files, `site/parts/docs.py`, `site/preview.py`,
  `tests/test_anim_figures.py`, and everything else.

The controller is regenerating all 55 figure pages and their stills (`content/anim/nf-*`)
while you work. If you need a figure still, the file may change under you; that is
expected.

## Added mid-round

- **editorial**: owns the professor's text changes of `tools/ROUND11_EDITS.md`:
  - in `site/build.py`: only the `PROF_RESEARCH`, `PROF_RESEARCH_MORE` and
    `PROF_MOTIVATION` blocks, `APPROVED_EDITS` and `deck_report`'s inputs, and the
    research page template (`<h2>The educational sections</h2>`);
  - `site/parts/motivation.py`, `site/parts/rboxes.py`, and the tests that pin those texts.
- **bpnav**: `site/parts/bpnav.py` and `tests/test_bpnav.py` (the column's Big Picture
  row). It may also edit the column rules in `site/parts/theme.py`, only if strictly
  needed.
- **Shared file:** `site/build.py` is now edited by two agents, deck and editorial.
  - Use targeted Edit calls only, and re-read the region right before each edit.
  - Never rewrite the whole file, never reformat it, and never touch the other agent's
    region.
