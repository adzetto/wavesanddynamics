# cv: his CV as a page (cv.html), from content/cv/cv.json

**Pipeline.** `python tools/cv_extract.py` reads `content/source/Korkut_Kaynardag_Resume.docx` (standard library only: zipfile and ElementTree) and writes `content/cv/cv.json`; `--check` writes nothing and exits 1 when the JSON no longer matches the Word file. Run it whenever he sends a new CV, then `python -m pytest -q tests/test_cv_extract.py`. The Word file never ships.

**Sanitised.** His CV's contact line holds a personal Gmail address and a personal phone number: neither is copied. `email` is always korkutkaynardag@iyte.edu.tr, `location` is the first part of that line ("Izmir, Turkiye"), and the "Personal webpage" link (this site) is dropped. Before writing, `leaks()` refuses a file that holds a Gmail address, any other email address, a `+` phone prefix or anything shaped like a phone number. A profile label it does not know (say "ORCID") stops the run until it gets a kind in `KINDS`; a line it cannot file stops it too, so nothing is dropped in silence.

**Word for word.** Every entry keeps his words, in his order, with his spelling ("Bogazici", "Turkey", "patent no:", the repeated journal name in publication 2, the $20,000 and $25,000 of the Proof of Concept award). Three things change and none of them is a word: runs of whitespace become one space; a heading or an organisation typed in capitals is set in title case (small words lower); and a separator between two facts (the em dash before a grant's amount, the dash of a date range, the " | " of an award, the tab before a date, the quotation marks around a title, "Role:") becomes a field boundary. The extractor checks each entry as it reads it (its fields hold exactly the words and figures of his line), and the tests read the Word file a second time, independently, and compare every section word for word.

## cv.json

```
{"name": "Korkut Kaynardag, Ph.D.", "location": "Izmir, Turkiye",
 "email": "korkutkaynardag@iyte.edu.tr",
 "links": [{"label": "Google Scholar", "href": "https://...", "kind": "scholar"}, ...],
 "areas": ["Structural Health Monitoring", ...],
 "sections": [{"id": "education", "title": "Education", "numbered": true?, "entries": [...]}]}
```

- `kind` is one of scholar, linkedin, researchgate, github, youtube, in his order.
- `areas`: his "Research Interests and Areas of Expertise" table read down its columns (monitoring, then dynamics and data, then modelling): 15 strings. The same list is that section's entries.
- `id`: a short anchor for each of his headings (`education`, `research-interests`, `experience`, `grants`, `journal-publications`, `conference-proceedings`, `conference-presentations`, `invited-talks`, `patents`, `awards`, `peer-review`, `workshops-and-memberships`, `certifications`); a new heading gets a slug of its title.
- `numbered`: present (true) where his CV numbers the list.
- Dates: `"MM/YYYY"`, `"YYYY"` or `"present"`; a single date is `date`, a range is `start` and `end`.

Entry types (`type`):

| type | fields | from his line |
|---|---|---|
| `position` | org, place, role, start, end | ORGANISATION (tab) place / role (tab) dates |
| `area` | text | a cell of his table |
| `grant` | title, amount?, date or start and end, line?, role? | title, dash, amount (tab) years / line / Role: ... |
| `citation` | authors [list], title, venue, year | authors "title", venue, year |
| `item` | title, detail?, date? | title \| detail (tab) date; a line ending in its month; "..., patent no: ..." |
| `group` | title, note?, numbered?, entries | his bold italic subheading: "Published (* stands for equal contribution)", "Workshops", "Memberships", "Certifications" |

## The page

`render(cv=None)` returns the body, `<div class="wrap cv">` and all (the root carries only its class, so build.py's `page()` recognises the wrapper). With no argument it reads the JSON itself (`load()`). `his(cv)` returns his words as the page prints them, HTML-escaped, for build.py's `VERBATIM` list: one of his proceedings titles has a spaced en dash ("model updating – seismic"), which the em dash report otherwise bills to this part. `SHORT` holds the Contents list's short names; each section keeps his heading.

- **Head:** "Curriculum vitae" (eyebrow), his name as the h1, place and email, then the page's one filled control, **Save as PDF** (`--accent`, `--btn-fg`, the brief's section 6 keeps it for the CV), then his five profiles. The button calls `print()` and exists only under `@media (scripting:enabled)`, so nothing moves when scripts arrive and nothing dead shows without them.
- **Entries:** what on the left, when on the right, on the first line's baseline. Titles serif 19px `--ink`; the lines under them 16px; dates, places and amounts sans 600 14px, lining tabular figures, right-aligned. A range is two `<time>` fields with a closed-up en dash. A position keeps his CV's two lines (organisation and place, role and dates). A grant: title and years, the line under it and the **amount** in its own right-hand field, then **Role** as a label and his role. A paper: title, authors (his name bold wherever it appears, star included), venue in `--muted`, year right; numbered in a 36px gutter where his CV numbers them. The research areas are his table: three columns read downward, a hairline over each cell, rows as tall as their tallest cell.
- **Contents:** from 860px of container width the CV (up to `--measure-wide`) has a 180px list beside it, sticky, with the docs' mark (one `--accent` line on a hairline track) sliding to the section in view: one IntersectionObserver over the sections, the top third of the window as the band, no scroll handler. Below 860px the same list folds into a `<details>` above the CV, shut by default, 44px rows in two columns. In the DOM the list comes before the sections.
- **Narrow (under 560px):** a position's place moves under its role, beside its dates.
- **Print (A4 or Letter, the reader's paper; named page `cv`):** no site column, bar, footer, skip link, eyebrow, button or Contents; white ground; link addresses printed beside their labels (links stay live in the PDF); entries never split, headings never end a page; "Curriculum Vitae" top right, his name bottom left, "1 / 5" bottom right. Those margin texts also keep Chrome from printing its own date, title and address, so the PDF is the same with "Headers and footers" ticked or not (an empty `content` does not do this). `beforeprint` names the saved file "Korkut Kaynardag CV". Checked by printing to PDF with headless Chrome at Letter and A4: five pages, fonts embedded, no header or footer from the browser.
- **Motion:** the Contents mark (240ms, `--ease`), the Save arrow dropping 2px on hover, the fold's chevron. Nothing loops. Under reduced motion build.py's floor drops every transition.
- **Checks (1280x800 and 390x844):** axe 0 violations (Contents shut and open), Lighthouse accessibility, best practices and SEO 100 on desktop and mobile, no horizontal scroll at 390px, keyboard path: column, email, Save as PDF, profiles, Contents, footer.

Scoped under `.cv`; tokens only (one numeric custom property, `--cv-rows`, set inline on the areas table); no side effects on import.
