# Round 4 spec (2026-09-24): binding for every agent in this round

Target: the static site in `site/` (the design source of truth). The Wix Studio copy is ported
later, after the user reviews this round. Do not touch any Wix site in this round.

## 0. Inputs (read them)
- `content/source/NEW WAVES AND DATA.pptx`: the professor's NEW 4-slide mockup (the old one is
  kept as `content/source/NEW WAVES AND DATA (2026-09-21).pptx`). Rendered slides:
  `reference/design-mockup/ppt-0924/slide-1.png` to `slide-4.png`. Slide 1 = home, 2 = About,
  3 = My Research Areas, 4 = the header band alone.
- `reference/design-mockup/hero-illustration-2026-09-24.jpeg` (1300x940): the home page
  illustration the user wants on index.html, animated with CSS/JS.
- `content/source/Korkut_Kaynardag_Resume.docx`: his CV. It contains a personal Gmail and a
  personal phone number: neither may appear anywhere on the site (section 8).
- The user's words (Turkish), summarised: add his CV; the JPEG illustration on the home page,
  much more beautiful with CSS animations and JS; the header band from the deck, done nicely in
  the site's style; About: a "Biography" heading, CV and profile links at the TOP (not the
  bottom), "At a glance" BELOW the career timeline, research areas in the right column so they
  show as soon as the page opens; rename Documents to something like "Big Picture of Waves and
  Data Analytics", but the vibration / signal processing / machine learning guides must show in
  the left column on their own, not under it; make "Contents" more prominent; make Contact much
  more beautiful; Machine Learning must open the document itself (no "Start here" page), with
  its recommended books at the end. Meeting note with the professor: a "Big picture of data and
  analytics" part covering Waves, Dynamics, Signal Processing, System Id., Estimation theory,
  Optimization, Machine learning, Python / programming; and Blog / Communication tips.

## 1. Binding design rules
- `site/design/DESIGN_BRIEF.md` stays binding (palette tokens, type scale, measure, hover
  vocabulary, reduced motion). Colours only from `site/parts/theme.py` tokens.
- Craft bar, read before designing: `C:\Users\lenovo\.claude\skills\apple-design\SKILL.md`
  (response, interruptibility, springs, reduced motion, transform/opacity only),
  `C:\Users\lenovo\.claude\skills\emil-design-eng\SKILL.md`,
  `C:\Users\lenovo\.claude\skills\animate\SKILL.md`; for reviewing motion
  `C:\Users\lenovo\.claude\skills\review-animations\SKILL.md`; accessibility
  `C:\Users\lenovo\.claude\plugins\cache\ecc\ecc\2.2.2\skills\accessibility\SKILL.md`.
- Airy, typographic researcher site (generic template looks were rejected before): no
  shadowed lifting cards, no stock icon packs, no filled nav-blue buttons, one warm accent.
- Motion: purposeful; every ambient loop pauses off-screen (IntersectionObserver) and when the
  tab is hidden; `prefers-reduced-motion: reduce` gives a complete static composition; animate
  transform / opacity / stroke-dashoffset only; no layout thrash; no CLS.

## 2. Information architecture (ruling)
The column, top to bottom (labels and sub-lines are his, from slide 1):

| # | row | sub-line | opens |
|---|---|---|---|
| 1 | About Me | | about.html |
| 2 | My Research Areas | Sound Waves, NDT, SHM | research.html |
| 3 | Gallery | | gallery.html |
| 4 | Big Picture of Waves and Data Analytics | | big-picture.html (replaces documents.html) |
| 5 | Vibrations and Waves | All vibrations are waves | doc/dynamical-behavior-of-engineering-structures-and-acoustic-wave-propagation.html |
| 6 | Signal Processing, System Identification | Estimation, Inverse Problems, Optimization, Machine Learning | doc/signal-processing-system-identification-and-optimization.html |
| 7 | Machine Learning | Neural and non-neural methods, Data Science vs ML Engineer | doc/machine-learning-the-complete-picture-and-guide-5.html |
| 8 | Probability, Statistics | Stochastic Process, Estimation | probability-statistics.html (in preparation) |
| 9 | Python / Programming | | python-programming.html (in preparation) |
| 10 | Communication | Meetings, presentations, reports, papers | communication.html (in preparation) |
| 11 | Blog | | blog.html |
| 12 | Contact | | contact.html |

- Group separators (existing "grp" style) before row 4 and before row 11.
- Row 4 has NO sub-items in the column; rows 5-10 are top-level rows, not its children.
- Marking: a doc page of rows 5-7 marks its own row (aria-current="page"); the three SHM/NDT
  documents mark row 2 (section); From Bridges to Photons marks row 4 (section); cv.html marks
  row 1 (section). The SUBNAV list under Documents goes away.
- Removed pages: documents.html, vibrations-waves.html, signal-processing.html,
  machine-learning.html. Every internal link that pointed at them is updated (home cards,
  research page, "Start here" rows, footer, gallery). `link_report()` must be clean.
- Sub-line typography: small (13px sans), light on navy with at least 4.5:1 contrast, 2 lines
  max. 12 rows should fit 1280x800 without the column scrolling if at all possible; below that
  the list scrolls inside the column (existing behaviour). Mobile drawer: same list.
- His "Meetings, presentations. Reports. papers" is shown as "Meetings, presentations,
  reports, papers" (separators normalised, words unchanged). Row titles drop the trailing comma
  the slide uses to continue into the sub-line.

## 3. Home page (index.html), top to bottom
1. **Masthead band** with his header text, verbatim (slides 1 and 4):
   "From elastic waves causing dynamic vibrations in a bridge to the matter waves inside a
   single atom (fun fact: roughly 7 × 10²⁷ atoms in a human body), wave motion sits at the
   center of the physical world. What we observe, though, arrives as discrete measurements.
   Data analytics is how we recover the information behind those numbers, and how we make it
   useful."  Render 10²⁷ as `10<sup>27</sup>` with proper sup styling. Deep navy band, light
   text, refined serif, generous leading, a quiet animated wave hairline (reduced motion:
   still). On desktop it should read as the top of the page like the slide (full-bleed above the
   column is preferred if the fixed column's name block is never hidden; otherwise across the
   main column). On phones it sits under the top bar. Home page only.
2. **Hero**: his intro (PROF_INTRO) on the left, the animated illustration (section 4) on the
   right, as slide 1. His "Myself:" paragraph (PROF_BIO) follows full width; keep the portrait
   and the contact bits (Izmir, the IYTE email) near it, smaller than today.
3. **Motivation** (existing part).
4. **Explore the topics**: six cards for rows 5-10, each with his sub-line as its text; three
   open the documents, three open in-preparation pages (marked subtly, still links). New icons
   for Probability & Statistics, Python / Programming, Communication in the existing icon style
   (28px line, one amber detail, the subject acted out on hover).

## 4. The hero illustration (site/parts/heroart.py)
Recreate the JPEG as inline SVG (no raster) with the same composition: left buildings; a
suspension bridge in the centre with a train on the deck; a wind turbine; right buildings; a
car; a chimney with smoke; an airplane top right; sensor rings on each structure joined by
dashed lines, and dashed links rising to three model diagrams at the top (a scatter plot with a
regression line and band, a small neural network, a decision tree with one highlighted path);
a soft mirrored reflection under the ground line; below it, a signal trace (impulses and
decaying oscillations) running into a ripple and turning into spectrum bars.
- Motion (the brief the judges score against): data packets travel from sensors up the dashed
  links to the models; sensor rings pulse in turn; turbine blades turn; the train crosses; the
  car drives; smoke rises; the plane glides; network activations propagate layer by layer; the
  tree path lights in sequence; regression points settle; the trace scrolls into the ripple and
  the bars breathe with it. One calm story, not noise: stagger, keep amplitude small.
- Interaction: hovering or focusing a structure highlights its sensor, its data path and the
  model it feeds; subtle pointer parallax on desktop is allowed.
- Palette: blue monochrome like the JPEG mapped to site tokens (nav navy for strong strokes,
  lighter tints for fills), at most one warm accent for the "insight" moment.
- Accessibility: role="img" with a concise aria-label; decorative parts aria-hidden; no traps.
- Performance: one inline SVG, CSS animations plus a small JS controller, pauses off-screen and
  on a hidden tab, reduced motion = static final frame, no CLS (reserve its box), markup under
  60 KB.
- Responsive: scales in the hero at 1280 and 1440; at 390 a simplified variant is fine.
- Interface: `render() -> str` returning the complete figure markup; CSS and JS as module
  strings like every part.

## 5. About page (about.html)
Order: H1 "About Me"; a profile header (portrait, "Korkut Kaynardag, PhD", role line) with the
actions row at the TOP: Download CV (to cv.html), Google Scholar, LinkedIn, ResearchGate, and
GitHub / YouTube as secondary; then two columns at desktop: left "Biography" (h2) with
PROF_ABOUT verbatim, carrying the bold emphasis of slide 2 (bold runs: "master's degrees",
"Boğaziçi University in 2013 and 2016", "Ph.D.", "The University of Texas at Austin in 2023",
"Applied Data Scientist at Transtek International Group", "Senior AI Engineer at Renesas
Electronics America", "Assistant Professor", "Izmir Institute of Technology"); right column,
visible above the fold at 1280x800: "Research areas", his CV list (`areas` in cv.json, his
words) with a link to My Research Areas. Then Career (the timeline part), then At a glance
BELOW it. Mobile: single column, actions stay near the top.

## 6. CV page (cv.html), new
Full CV from `content/cv/cv.json` (generated by `tools/cv_extract.py` from the docx),
sanitised: location "Izmir, Turkiye", email korkutkaynardag@iyte.edu.tr, no phone. Elegant
academic CV typography, section anchors, his name bold in author lists, the "* stands for
equal contribution" note kept; dates right-aligned on wide screens; a "Save as PDF" button
(window.print) with a print stylesheet producing a clean A4/Letter PDF (no column, no
masthead, link URLs printed). Where his CV uses a dash as a separator (a grant amount, a
date range), render the parts as separate fields, never an em dash. Not a column row; row 1
is marked.

cv.json schema (the CV owner defines the entry details and documents them in
`site/parts/cv.md`): `{"name", "location", "email", "links":[{"label","href","kind"}],
"areas":[str], "sections":[{"id","title","entries":[...]}]}` with kind in scholar,
linkedin, researchgate, github, youtube (the "Personal webpage" line is this site: drop it).

## 7. Other pages
- **Contact**: much more beautiful. Email card with a copy button and mailto (IYTE only);
  Department of Civil Engineering, Izmir Institute of Technology, Izmir, Turkiye; profile links
  (from cv.json) with small line glyphs; Download CV; a quiet visual motif consistent with the
  hero (for example a ripple or a signal line). No form, no map embed, no third-party requests,
  no "coming soon" filler.
- **Big Picture of Waves and Data Analytics** (big-picture.html): H1 that title; the topics of
  the meeting note (Waves, Dynamics, Signal Processing, System Identification, Estimation
  Theory, Optimization, Machine Learning, Probability & Statistics, Python / Programming,
  Communication) each pointing to its document or in-preparation page; a group for the SHM/NDT
  documents from his research; From Bridges to Photons under Waves. An interactive concept map
  (physics to measurement to data analytics) is welcome if it stays calm and accessible. Our
  text = labels and the existing one-line notes only.
- **In-preparation pages** (probability-statistics, python-programming, communication): H1 his
  label, his sub-line, a refined "In preparation" state, links to related existing documents.
  No invented content.
- **Document pages**: "Contents" more prominent (clearer label and toggle, tinted card,
  numbered entries, bigger targets) while staying collapsible with zero footprint when closed.
  Rows 5-7 open these pages directly; their book sections (Recommended Books / The Books / Go
  Deeper With Books) are already at the end of the documents.

## 8. Content rules (checked by `python site/build.py --strict`)
- His text verbatim: PROF_* constants plus a new PROF_HEADER; `DECK` points at the new deck and
  `deck_report()` checks PROF_HEADER against slide 1.
- No em dashes in our text. Only email: korkutkaynardag@iyte.edu.tr. No phone number and no
  Gmail anywhere (grep the built site for "gmail" and "300-4065").
- The CV docx is never published; only the cv.json-derived HTML.

## 9. Engineering rules
- Parts pattern: `CSS`, `JS` module strings plus render functions; selectors scoped; tokens only.
- Build to your OWN output dir: `python site/build.py --out build/r4/<your-name>`; serve it on
  your own port; never write site/dist (only the integrator does). If a build fails inside a
  file you do not own, wait and retry; do not edit other owners' files.
- Tests: `python -m pytest -q` must pass; `ruff check` clean for the files you touch.
- Browser checks: chrome-devtools MCP pages with your own `isolatedContext` name; close them.

## 10. Interfaces the shell owner wires (build.py calls these through `call()`)
- `masthead.render(text_html) -> str`
- `heroart.render() -> str`
- `hero.render(contact=None, intro=None, bio=None, art=None) -> str`
- `topics.render(items=None) -> str`; item = dict(href, title, sub, icon, soon)
- `about.render_page(about_html, links, areas, timeline_html) -> str` (glance inside, below)
- `cv.render(cv) -> str` (the page body from cv.json)
- `contact.render(info) -> str`; info = dict(email, department, institute, city, country,
  links, cv_href)
- `documents.render_big_picture(docs) -> str` (docs = build.DOCS; the topic to slug grouping
  lives in the part)
- `soon.render(title, sub, related) -> str`; related = list of dict(href, title)
- `docs.py` keeps its API.

## 11. Gates for "done"
`python site/build.py --strict` passes; link report clean; axe 0 violations on every page;
Lighthouse accessibility / best practices / SEO 100 on index, about, cv, contact, big-picture
and one doc; no console errors; CLS under 0.05 on index; a keyboard path through column, hero
and cards; reduced motion checked; screenshots at 1280x800 and 390x844 for every page into
build/r4/shots/.

## 12. Addendum (user, 2026-09-24): profile links, exact
Use exactly these three profile URLs on About and Contact, and nowhere else invent others:
- LinkedIn: https://www.linkedin.com/in/korkutkaynardag
- Google Scholar: https://scholar.google.com/citations?user=v_eQpwUAAAAJ&hl=en
- ResearchGate: https://www.researchgate.net/profile/Korkut-Kaynardag
About and Contact show only these three (as slide 2 does), plus the CV link. GitHub and YouTube
appear only on cv.html, because they are part of his CV header. In cv.json the LinkedIn href
is the URL above (no trailing slash).
