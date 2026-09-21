# CONTENT INVENTORY — wavesanddata rebuild (from v01–v07 + image01)

## A. Canonical site map

Two nav generations exist in the footage. **v01–v06 (all clips) show a top bar with wordmark-left + hamburger-right and NO sidebar. image01 (the still) is the only frame showing the persistent left sidebar** — that is the later, approved state ("sol kisimda menu olcak hep") and is the canonical nav. Everything below is ordered by the sidebar.

| # | Nav label | Route (evidence) | Filmed? |
|---|---|---|---|
| 1 | Home | `/` — page selector reads "Homepage" (v02) | v02 full page + image01 (sidebar layout) |
| 2 | About Me | `/about` (v01 toolbar) | v01, full page |
| 3 | My Research Areas | `/research` (v03, v05 toolbars) | v03 partial, v05 fuller |
| 4 | Gallery | not observed; referenced in `/research` copy | NEVER |
| 5 | Vibrations and Waves | `/vibrations-waves` (v04 toolbar, kebab-case) | v04, full page |
| 6 | Signal Processing & Optimization<br>↳ sub-label: *System Identification · Estimation · Optimization* | not observed | NEVER |
| 7 | Machine Learning | not observed | NEVER as a web page; source content = v07 Word doc |
| 8 | Blog | not observed | NEVER |
| 9+ | **list is cut off below "Blog"** — scrollbar thumb does not reach track bottom | — | Contact exists as a built page (`/contact`, v06) but is not visible in the sidebar crop; further items unknown |

Sidebar header block (above nav): circular headshot → serif "Korkut Kaynardag, PhD" → "Assistant Professor, Department of Civil Engineering" / "Izmir Institute of Technology".

Builder project handle (for recovering real source instead of rebuilding from video): project **`34000a66-3304-4430-a914-5c4a1656cce7`**, name **"Korkut's Research Hub"**, conversation tail `…52ce-4af7-8d44-37ec65de63bb`, chat title "Build webpage with provided files". (Host string reads `lovable.dev` in v02 and `claude.ai` in v03/v06 — the uuids are identical in both, so it is one project; confirm which account holds it.)

---

## B. Page-by-page inventory

### 1. Home — `/` (v02 complete, scrolled 0→100%; image01 = same copy in sidebar layout)
Page is exactly three blocks, **no footer** (scrollbar reaches track bottom in v02_019/020).

| Section | Content | Status |
|---|---|---|
| Eyebrow | "ACADEMIC & RESEARCH PORTFOLIO" | REAL |
| H1 | "Korkut Kaynardag, PhD" (duplicates the wordmark/sidebar name) | REAL |
| Hero ¶1 | "This webpage introduces you to three things: **myself**, **my research**, and **the topics I use in my research** — on the mechanics and physics side, wave propagation and dynamics; on the data side, AI, signal processing, system identification, optimization and estimation." (three bold runs) | REAL |
| Hero ¶2 | "I am an Assistant Professor in the Department of Civil Engineering at Izmir Institute of Technology, specializing in structural health monitoring (SHM), non-destructive testing (NDT) and sound target analysis — deployed offline through developed software and tools, via cloud data processing, or on-board via microchips." | REAL |
| Hero CTAs | "About me →" (primary, blue) → `/about`; "My research areas" (secondary) → `/research` | REAL, targets unverified |
| Headshot | brick-wall portrait, ~1:1 | REAL (needs full-res original) |
| H2 "Why the educational sections exist" | intro ¶ + ordered list of 4 questions (item 4 contains italic "*Aha!*") + closing ¶ ("Had I started learning with the answers to those four questions…") | REAL, complete |
| H2 "Explore the topics" | 3 cards, each = title + 1-sentence body + "Read more →": **Vibrations and Waves** / **Signal Processing & Optimization** / **Machine Learning** | REAL |
| Footer | none | **MISSING** |

### 2. About Me — `/about` (v01 complete)

| Section | Content | Status |
|---|---|---|
| H1 | "About Me" | REAL |
| Profile link row | "Google Scholar — link coming soon", "LinkedIn — link coming soon", "ResearchGate — link coming soon" (plain muted text, not anchors) | **PLACEHOLDER ×3** |
| H2 "Biography" | 4 full paragraphs (degrees, assistantships, industry, IZTECH, asset list) | REAL, complete |
| Media rail | portrait photo; "⤓ Download CV (coming soon)" button; caption "Placeholder — the CV file will be attached here." | **PLACEHOLDER** (button is non-functional) |
| H2 "At a glance — September 2026" | 3 stats: **12** Published articles · **2** Patents — 1 granted, 1 pending · **8** Awards from academic & industry-academia grants | REAL but hard-dated; underlying lists absent |
| H2 "Career timeline" | 5 entries (see facts, §D) | REAL, complete |
| Footer | none (page bottom reached) | **MISSING** |

### 3. My Research Areas — `/research` (v03 + v05; v05 is the later/fuller state)

| Section | Content | Status |
|---|---|---|
| H1 + lede | "My Research Areas" + "My research focuses on Structural Health Monitoring (SHM) and Non-Destructive Testing (NDT): the science of monitoring and testing structures to detect and characterize defects before they become failures." | REAL |
| H2 "Overview" | 2 paragraphs (industry path as Senior AI Engineer on sound source tracking; "You'll also find these documents under the Gallery section…"; "everyone's path is different…") | REAL, complete |
| H2 "Research areas" | 2×2 grid, 4 cells: **Structural Health Monitoring & Non-Destructive Testing** / **Vibration Analysis & Acoustic Wave Propagation** / **Sound Source Tracking** / **Data Analytics & Machine Learning**, each with a 1–3 line body | REAL, complete |
| H2 "Introductory documents" | 4 rows (v03 shows only rows 1–2; v05 shows all 4): 1) "SHM / NDT — Short Introduction" — *Word / PDF document — coming soon* 2) "SHM / NDT — Extended Document" — same 3) "Sound Wave Tracking" — same 4) "Extensive Presentation on my M.Sc. and Ph.D. Research" — *PowerPoint document — coming soon*. Each with a right-aligned "⤓ Download". | **PLACEHOLDER ×4** — Download links point at nothing |
| H2 "Also on this site" | cross-link paragraph quoting the nav labels: *"Are you also asking about the "Vibrations and Waves", "Signal Processing, System Identification, Estimation, Optimization" and "Machine Learning" sections in the menu? I explain those topics in a…"* | **TRUNCATED** — sentence cut off by viewport; clip never scrolls further |
| Below that | ~20–25% of the page (scrollbar) was never filmed — may contain more content and/or a footer | **UNKNOWN** |

### 4. Vibrations and Waves — `/vibrations-waves` (v04 complete; **this is the template for every topic page**)

| Section | Content | Status |
|---|---|---|
| H1 + lede | "Vibrations and Waves" + "The mechanics and physics side of my research: wave propagation and dynamics. This section is written for newcomers — the overall picture, the intuition, and how the topic connects to signal processing and machine learning." | REAL |
| H2 "The big picture" | "[Content coming soon — this section will answer: when vibration and wave methods are used, what problems they solve, where similar ideas appear across applications, and how they connect to the data side of structural health monitoring.]" | **PLACEHOLDER** (bracketed italic) |
| H2 "How to learn this topic" | "[Content coming soon — a recommended learning path based on my own experience moving from civil engineering into wave propagation and dynamics.]" | **PLACEHOLDER** |
| H2 "Recommended books & resources" | "[Content coming soon — the books I found most useful, in the sense that they contain the most complete and clearest explanations of the topic.]" | **PLACEHOLDER** |
| H2 "Documents" | 1 row: "Vibrations and Waves — Notes & Guide" / "Word / PDF document — coming soon" / "Placeholder for the downloadable Word document for this section." / Download | **PLACEHOLDER** |
| Figures | none, and no figure slots stubbed — on the site's most visual topic | **MISSING** |
| Footer | nothing below the document row | **MISSING** |

### 5. Signal Processing & Optimization — route unknown
Never filmed. Evidence of existence: sidebar item + sub-label "System Identification · Estimation · Optimization", homepage card ("Signal processing, system identification, estimation and optimization — the data side."), and the `/research` cross-link paragraph. **Assume the v04 template (lede → big picture → how to learn → books → documents) but this is inference, not observation.**

### 6. Machine Learning — route unknown
Never filmed as a web page. **The content exists and is finished** as a Word document (v07): *"Machine Learning - The Complete Picture and Guide_5"*, 9,246 words, ≥40 pages, with its own 12-item TOC:

1. What is Machine Learning? (p2) · 2. More Usage Examples, by Domain (6) · 3. Features, Preprocessing, and Feature Engineering (8) · 4. Non-Neural Network Models (12) · 5. The Neural Network Core (19) · 6. Neural Networks for Specific Tasks (22) · 7. Reinforcement Learning: Learning by Trial and Error (27) · 8. Wrap-Up: When to Use What (32) · 9. Evaluating Model Performance (33) · 10. Using Machine Learning Responsibly *(ironically, this section was drafted by AI, but fact-checked by me)* (37) · 11. Glossary (39) · 12. How to Learn Machine Learning (40)

Sub-sections evidenced: 1.1, 1.2, 3.2, 3.3, 3.4, 3.6, 4.1, 4.2, 4.4, 4.5. Figures evidenced: 3, 4, 6, 7, 8, 9, 13 (+ references to 2, 5, 11, 12). Only sections 1–4.5 are visible in the clip; **5–12 exist per the TOC but were never shown**. Contains one external hyperlink (StatQuest YouTube) and his email in a Disclaimer box.

### 7. Gallery — route unknown
Never filmed. Promised twice by `/research` copy as the place where the introductory documents also live. **No design, no content, no item list in hand.**

### 8. Blog — route unknown
Nav item only. No post list, no post template, no post content in any frame.

### 9. Contact — `/contact` (v06 complete to the last visible row)

| Section | Content | Status |
|---|---|---|
| H1 + lead | "Contact" + "Feel free to reach out about research, collaboration, or the educational sections of this site — especially if you are a student or newcomer to these topics." | REAL |
| H2 "Where to find me" | • Department of Civil Engineering / Izmir Institute of Technology, Izmir, Turkey — REAL<br>• Email / "[Email address coming soon]" — **PLACEHOLDER**<br>• Office / "[Office details coming soon]" — **PLACEHOLDER** | mixed |
| H2 "Elsewhere" | "My academic profiles and CV will be linked here." + Google Scholar / LinkedIn / ResearchGate, each "— link coming soon" | **PLACEHOLDER ×3** |
| Absent | no phone, no office hours, no contact form, no map, no working mailto | **MISSING** |
| Footer | never reached | UNKNOWN |

---

## C. Placeholder register (everything that says "coming soon")

1. `/about` — Google Scholar link
2. `/about` — LinkedIn link
3. `/about` — ResearchGate link
4. `/about` — Download CV button + "Placeholder — the CV file will be attached here."
5. `/research` — SHM/NDT Short Introduction (Word/PDF)
6. `/research` — SHM/NDT Extended Document (Word/PDF)
7. `/research` — Sound Wave Tracking (Word/PDF)
8. `/research` — Extensive Presentation on M.Sc. and Ph.D. Research (PowerPoint)
9. `/vibrations-waves` — "The big picture" body
10. `/vibrations-waves` — "How to learn this topic" body
11. `/vibrations-waves` — "Recommended books & resources" body
12. `/vibrations-waves` — Notes & Guide document
13. `/contact` — Email address
14. `/contact` — Office details
15. `/contact` — Google Scholar / LinkedIn / ResearchGate (×3)
16. Implied ×2 pages — the same items 9–12 for Signal Processing & Optimization and Machine Learning

**Count: ~24 named placeholder slots on 4 filmed pages.** The design is finished; the payload is not. This matches his own statement that only the build remains — but note the build he means is the shell, not the files.

---

## D. Biographical & academic facts stated (verbatim source)

**Identity**
- Name as rendered site-wide: **"Korkut Kaynardag, PhD"** — ASCII, no `ğ`. Word doc title page uses "Dr. Korkut Kaynardag".
- Degree styling is inconsistent in-source: `PhD` (wordmark, hero), `Ph.D.` (biography, timeline), "master's and PhD" (research overview), "M.Sc. and Ph.D." (document title).

**Education**
- B.Sc. Civil Engineering, **Boğaziçi University**, **2013**
- M.Sc. Civil Engineering, **Boğaziçi University**, **2016**
- Ph.D. Civil Engineering, **The University of Texas at Austin**, **2023**

**Positions (chronological)**
| Years | Role | Institution / Location | Focus |
|---|---|---|---|
| 2013–2014 | Project assistant | Boğaziçi University, Istanbul, Turkey | SHM & NDT systems |
| 2014–2016 | Research assistant | Boğaziçi University | SHM & NDT systems |
| 2016–2023 | Ph.D. & Graduate Research Assistant | UT Austin, Texas, USA | Product- and service-oriented research on SHM and non-destructive testing systems |
| 2023–2024 | Applied Data Scientist | Transtek International Group, Florida, USA | Bridge and road monitoring solutions |
| 2024–2026 | Senior AI Engineer | Renesas Electronics America, Maryland, USA | Acoustic wave-based vehicle monitoring; sound source tracking |
| 2026–present | Assistant Professor | Department of Civil Engineering, Izmir Institute of Technology | SHM, nondestructive damage detection, smart sensors, smart cities |

- Start date at IZTECH stated precisely: **"Since August 27, 2026"**.

**Metrics (as of September 2026)**
- 12 published articles
- 2 patents — 1 granted, 1 pending
- 8 awards from academic & industry-academia grants
(No underlying list for any of the three exists anywhere in the material.)

**Research vocabulary (use verbatim)**
structural health monitoring (SHM) · non-destructive testing (NDT) / nondestructive damage detection · sound target analysis / sound source tracking · wave propagation and dynamics · vibration analysis · acoustic wave propagation · smart sensors · smart cities · AI · signal processing · system identification · estimation · optimization · machine learning · data analytics. Explicit split he uses: **"the mechanics and physics side"** vs **"the data side"** — the site's IA mirrors it.

**Structures/assets worked on**
tall buildings · masonry buildings and bridges · a suspension bridge · wind turbines · railway tracks · vehicles.

**Deployment modes (stated as a deliberate triple)**
"deployed offline through developed software and tools, via cloud data processing, or on-board via microchips" (edge AI).

**Contact data actually in hand**
- Institutional affiliation: Department of Civil Engineering, Izmir Institute of Technology, Izmir, Turkey
- Email: **korkut.kaynardag@gmail.com** — appears only in the Word document's Disclaimer box, **not on the site**. Personal Gmail, not the IZTECH address. Needs a decision before publishing.
- Office: unknown. Phone: none. Social/academic profile URLs: none.
- Domain he wants: **wavesanddata.com** (from his own chat message; custom-domain step was still pending in the builder). Note: the strings "Waves and Data" / "wavesanddata" appear **nowhere on the rendered site** — the brand is currently only the personal name.

---

## E. Comparison with the existing Wix site

### CARRIED OVER (same page exists in both, content rebuilt)
| Wix | Mockup | Notes |
|---|---|---|
| `/` | Home | Entirely rewritten. New hero copy, new "Why the educational sections exist" essay, new 3-card grid. |
| `/personal-resume` | **About Me** (`/about`) | Renamed. Bio is prose, not a CV table. Gains stat band + career timeline + CV download slot. URL changes → redirect needed. |
| `/research-portfolio` | **My Research Areas** (`/research`) | Renamed. The word "portfolio" survives only in the homepage eyebrow "ACADEMIC & RESEARCH PORTFOLIO". URL changes → redirect. |
| `/structural-dynamics-and-wave-propagation` | **Vibrations and Waves** (`/vibrations-waves`) | Renamed **and rescoped** — "structural dynamics" is dropped from the title; new lede frames it as "the mechanics and physics side". URL changes → redirect. |
| `/contact` | **Contact** (`/contact`) | Same route. Content is thinner than a normal contact page (no form, no phone, no map) and email/office are placeholders. |
| `/gallery` | **Gallery** | Route/nav survives; **zero design or content evidence in any frame**. Now has a dependency: `/research` copy promises the introductory documents live here. |
| `/blog` | **Blog** | Nav item survives; nothing else. 8 posts (Feb–Apr 2022) have no representation in any mockup. |

### SPLIT (1 Wix page → 2 mockup pages)
- `/signal-processing-optimization-ml` → **"Signal Processing & Optimization"** (with sub-label *System Identification · Estimation · Optimization*) **+ "Machine Learning"** as two separate top-level nav items and two separate pages. This is the single biggest structural change to the IA, and neither page has been filmed.

### NEW (no Wix equivalent)
1. **Persistent left sidebar** with circular avatar, name, and affiliation block — his one explicit requirement, and present in only one artifact (image01).
2. **Nav sub-labels** (one item only, so far).
3. **"Why the educational sections exist"** — the pedagogical rationale essay + 4 numbered questions. Entirely new voice/section for the site.
4. **"Explore the topics"** 3-card grid on the homepage.
5. **Educational topic-page template**: lede → "The big picture" → "How to learn this topic" → "Recommended books & resources" → "Documents". Repeats across 3 topic pages.
6. **"At a glance"** stat band (12 / 2 / 8).
7. **Career timeline** component (5 entries).
8. **"Introductory documents"** download list on `/research` (4 rows, icon + title + type/status + Download).
9. **"Also on this site"** in-prose cross-link block.
10. **"Elsewhere"** academic-profile block on `/contact`.
11. **Explicit CV download slot**.
12. **Machine Learning long-form guide** as site content (9,246 words, 12 sections) — this alone is larger than the entire rest of the site.

### DROPPED / absent from every mockup
1. **`/fullscreen-page`** — the Wix orphan. Nothing corresponds; delete or 410/redirect.
2. **Footer** — there is no footer on any of the five fully-scrolled pages (Home confirmed to 100%, About confirmed, Vibrations confirmed, Contact and Research not reached). No copyright line, no contact block, no affiliation logos, no social links, no back-to-top.
3. **Publications list** — 12 articles are counted but never listed. No page, no section, no nav item.
4. **Patents list** — 2 counted, never listed.
5. **Awards/grants list** — 8 counted, never listed.
6. **Teaching / courses** — no page, no mention.
7. **Students / research group** — none.
8. **News / announcements** — none.
9. **Search, breadcrumbs, table of contents, tags, dates, RSS** — none anywhere.
10. **Blog post content** — no template, no list page, no single post in any frame; nothing indicates the 2022 posts are being migrated.

---

## F. Content we do NOT have in hand

**Blocking (site cannot ship without a decision)**
1. **Email address to publish** — gmail vs IZTECH institutional.
2. **Office details** — building, room, hours.
3. **Google Scholar / LinkedIn / ResearchGate URLs** (used in two places each: `/about` and `/contact`).
4. **CV file** (PDF).
5. **Footer content** — or an explicit decision that there is none.
6. **Blog decision** — migrate the 8 posts from Wix, archive them, or drop the nav item. No post data is in hand: titles, bodies, images, dates, slugs all need exporting from Wix.
7. **Redirect map** — `/personal-resume`, `/research-portfolio`, `/structural-dynamics-and-wave-propagation`, `/signal-processing-optimization-ml`, `/fullscreen-page` all change or disappear.

**Content payload (exists per his statement, not in these frames)**
8. The **4 introductory documents** for `/research` (SHM/NDT short, SHM/NDT extended, Sound Wave Tracking, M.Sc./Ph.D. presentation).
9. **Vibrations and Waves — Notes & Guide** document.
10. **Body copy for 9 placeholder sections**: "The big picture", "How to learn this topic", "Recommended books & resources" × 3 topic pages (Vibrations, Signal Processing, Machine Learning).
11. **The Machine Learning .docx itself** — "Machine Learning - The Complete Picture and Guide_5.docx". Sections 5–12 (pp. 19–40+) were never shown; the whole file is needed. Also its figures 1–13, of which 1, 2, 5, 10, 11, 12 were never seen.
12. **Figures for every other topic page** — he says "tum icerigi ve figurleri… hazirladim", but no figure appears on any topic page in any clip, and no figure slots are stubbed.
13. **Gallery contents** — the entire page: what it holds, how many items, captions.
14. **Signal Processing & Optimization page** — never filmed; assumed to follow the v04 template.
15. **Publications (12), patents (2), awards (8)** — the underlying records behind the stat band.

**Unrecorded page regions**
16. Tail of the `/research` "Also on this site" sentence, plus roughly the bottom 20–25% of that page.
17. Sidebar nav items below "Blog" — the list is cut off; at minimum Contact is missing from the visible crop.
18. The top of the sidebar above the avatar (clipped) — any site logo/wordmark there is unknown.

**Assets**
19. **Full-resolution headshot** (brick wall, blue/mint striped shirt) — only exists as video frames; the original is in the "Korkut's Research Hub" project.
20. **The original project source** — exporting HTML/CSS from project `34000a66-3304-4430-a914-5c4a1656cce7` would replace every reverse-engineered measurement in these reads.

---

## G. In-source inconsistencies to resolve before building (do not silently normalise)

- **Same topic, three names**: "Sound Source Tracking" (research card) / "Sound Wave Tracking" (document row) / "Acoustic wave-based monitoring" (card body).
- **`&` vs `/`**: "Structural Health Monitoring **&** Non-Destructive Testing" (grid) vs "Structural Health Monitoring **/** Non-Destructive Testing" (document titles).
- **"nondestructive" vs "non-destructive"** — both appear, on the same page.
- **PhD / Ph.D. / "master's and PhD" / "M.Sc. and Ph.D."** — four stylings.
- **Dashes**: biography uses unspaced en dash in parens "(2023–2024)"; timeline uses spaced em dash "2024 — 2026".
- **Turkish diacritics dropped throughout**: "Kaynardag" (not Kaynardağ), "Izmir" (not İzmir), "Istanbul" (not İstanbul), "Turkey" (not Türkiye) — while "Boğaziçi" **is** correctly accented on the same line. Needs one decision applied consistently.
- **Topic order differs** between the homepage hero ("AI, signal processing, system identification, optimization and estimation") and card 2 ("Signal processing, system identification, estimation and optimization").
- **Homepage H1 duplicates the wordmark/sidebar name** — the name appears twice within 120px.
- **"At a glance — September 2026"** is hard-dated and will silently go stale; no "last updated" mechanism.
- **Brand mismatch**: the site is branded "Korkut Kaynardag, PhD" everywhere; "Waves and Data" / wavesanddata.com exists only as the target domain. Confirm whether the site should carry the Waves and Data name at all.
- **Machine Learning doc internal**: body says "Figure 11", the caption below it says "Figure 13"; "multi-layer perception" vs "Multilayer Perceptron"; "and the any setting" (likely typo); one unrendered emoji glyph.