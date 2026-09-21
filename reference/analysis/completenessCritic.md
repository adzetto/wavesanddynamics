## COMPLETENESS CRITIC — what is still missing, unverified, or self-contradictory

Scope checked: 7 clips (152 frames), 1 still, plus the on-disk corpus (`C:\Users\lenovo\Documents\wavesanddata` and the WhatsApp export at `C:\Users\lenovo\Downloads\+1 (512) 300-4065`). Ranked by damage to the rebuild.

---

### TIER 1 — would make the rebuild wrong, not merely imprecise

**1. The one thing he explicitly demanded rests on a single 576×1024 WhatsApp-compressed JPEG.**
`reference/design-mockup/frames/image01.jpeg` — 79,267 bytes, 576×1024, verified — is the *only* artefact in the entire corpus showing a left sidebar. Every sidebar fact the rebuild will use (nav order, 8 items, one 5% left gutter, 47px row pitch, 3-part active state, cream-vs-white two-tone, 36.6% circular avatar) comes from that one photo, at the lowest resolution of anything in the set, with the top clipped mid-forehead and the bottom clipped mid-"Blog". There is no second frame, no scroll, no hover, no second angle. All 7 videos contradict it (top-right hamburger, no sidebar). If that JPEG is a discarded experiment rather than the approved shell, the whole shell is built on nothing.

**2. Chronology of the 8 artefacts is unestablished, so "which draft did he like" is literally unknown.**
The analysis never records which `vNN` maps to which file. I reconstructed it by duration×bitrate: v01=`15.47.16`, v02=`15.47.16_2`, v03=`15.47.17`, v04=`15.47.17_2`, v05=`15.47.19`, v06=`15.47.20`, v07=`15.49.02`; image01=`WhatsApp Image … 15.47.17`. That is useless for ordering — all 8 were uploaded inside a 4-second album burst on 21 Sep, while the content was filmed ~6 days earlier (taskbar 9/15/2026). So: **nothing in the artefacts dates the drafts relative to each other.** And `v03` vs `v05` prove there are at least two iterations of the same `/research` page (v03: 2 document rows, no "Also on this site"; v05: 4 document rows + "Also on this site"). We are reverse-engineering a moving target and cannot tell which frame is the newest.

**3. His sentence is ambiguous and the whole brief hinges on it.**
"Bu taslagi beyenmistim mesala, renkler dizayn falan, sol kisimda menu olcak hep." Singular *"bu taslak"* after an 8-item album. Two incompatible readings: (a) descriptive — *this* draft is the one with the left menu, i.e. image01 is the approved shell and the hamburger clips are dead ends; (b) prescriptive — he liked the colours/design of the drafts and is *adding* a left-menu requirement they do not satisfy. `PROJECT.md` has already committed to reading (b). Nobody has asked him. One question resolves it and it changes the shell.

**4. There is no approved design for ~90% of the actual site.**
The drafts cover Home, About, Research, Contact and one *empty* topic shell (`/vibrations-waves`, all three sections literally `[Content coming soon — …]`). The real site is two ~3,300-word educational sections (19 and 24 figures) plus a 9,246-word ML guide with tables, callouts, figure captions and a 12-item TOC. **Zero frames show a long document page rendered on the web.** No evidence exists for: in-page TOC, figure+caption styling, table styling, callout/aside styling, equation rendering, a finished download button, per-section PDF link, blog index, blog post layout, gallery layout, publications list, 404, dark mode, search. The v07 clip shows that content's *Word* styling, which is a third visual language (terracotta H1s, blush callouts, peach table headers) unrelated to the ivory/serif web drafts. The first-pass claim that the Word palette is "very likely the palette he liked for the site" is an **inference presented as near-fact** — he said "beyendim" about the site drafts, not about the .docx.

**5. No single accent colour is established; the drafts disagree with each other.**
v01 About: brick red ≈#8E2B24 on stats/timeline dots *plus* a slate blue-grey CV button (#6E7F8C). v02 Home: exactly one saturated accent and it is **royal blue** #2C5FA3. v06 Contact: the only saturated colour is a rose/crimson icon stroke (the v06 critic measured B≈G and put the hue at 340–350°, explicitly rejecting the first pass's terracotta). image01: brick-red active bar + a distinctly **navy** H1. Four pages, four accent stories. A rebuilder picking one will contradict at least two "approved" frames.

**6. Every colour value in the corpus is a reconstruction, not a measurement.**
No neutral reference exists in any frame. Phone-on-monitor capture, warm auto-WB, glare bloom, exposure falloff to frame right/bottom. v03's first pass quoted hexes that are not within 40 RGB points of the actual pixels; v02's first pass read camera illumination as a 135° CSS gradient (debunked); v01's critic reversed the background's warmth direction. **Not one hex in this corpus should be typed into CSS.** Only the *relationships* survive (sidebar warmer than content; active row ~6% darker; accent = the brick from the portrait).

---

### TIER 2 — internal contradictions that must be resolved before building

**7. Which tool built the drafts — 3 of 7 clips disagree with the other 4, on identical UUIDs.**
v02 reads the address bar character by character as `https://lovable.dev/chats/9994de28-…?artifact=project%3A34000a66-…` and reads the composer placeholder "Ask Lovable anything…". v01 and v04 also say Lovable. v03, v05 and v06 call the *same chrome with the same UUIDs* "claude.ai Claude Artifacts" and cite the URL shape as proof. They cannot both be right. His own words: he used **Lovable** to turn the PPT into the design, and **Claude** to write the content/figures. Practical cost: chasing the wrong account to recover the source.

**8. The UUIDs are mutually inconsistent at character level — none of them is safe to type.**
Chat id: `4af7` (v02, v06) vs `4a17` (v03); `9994de28` vs `9994da28` vs `1994de28` (v05); `37ec65de63bb` vs `37ec65da63bb`. Artifact id tail: `5c4a1656cce7` (v02, v03, v06) vs `5c4b1856ce87` (v05, asserted "confirmed" by its own critic). The leading 8-char group is off-screen in v03 and v06 entirely. Anyone pasting these will get a 404.

**9. The /research "Research areas" grid — the page's signature block — has two opposite verified readings.**
v03's critic measured **four separately bordered boxes** with ~18px gaps (broken rules across the gutter, two parallel verticals, box tops and bottoms). v05's critic measured **no vertical divider, no row rule, no borders at all** — plain text blocks with 24px internal padding, and explicitly showed the dips are moire. Same component, same page, opposite conclusions, both with pixel evidence. Unresolvable from this footage.

**10. v04's two critics contradict each other on the header — and it changes the markup.**
Critic #1: the first hairline is an in-flow page rule after a top spacer; the byline is a bare fixed element. Critic #2: the first hairline is the **fixed masthead's bottom border**, present in all 9 frames including fully scrolled, and the masthead is **opaque and occludes scrolling content** (proved by the H2 "How to learn this topic" vanishing where it should be visible). Mutually exclusive. Same disagreement on the footer: #1 says the pane bottom is never in shot so "no footer" is unverifiable; #2 says it is confirmed at true bottom of scroll.

**11. Footer status is contradictory or unknown on every page except Home.**
v02: both critics prove 100% scroll → homepage has **no footer**, the card grid is the last element. v01: critic #1 says the thumb reaches the bottom (no footer, proven); critic #2 says it stops short (unknown). v03, v04, v05, v06: bottom never reached — v05's critic estimates ~20–25% of `/research` was never filmed. So we do not know whether the site has a footer at all, and the Contact page's "Elsewhere" row is the last thing ever seen there.

**12. Viewport widths are irreconcilable, which invalidates every absolute px figure across the seven reports.**
v01 critic: ~1050–1175 CSS px. v02 critic: ~1350–1450. v03 critic: ~1145–1150. v05 critic: ~1280×760. v06 critic: ≥1110 and the right edge is off-frame. v01 and v02 were filmed **one minute apart** on the same machine (10:08 and 10:07, 9/15/2026) yet differ by ~30%. Every type size, gutter and radius in all seven reports was derived from an assumed scale factor. They are not comparable to each other and none is trustworthy in absolute px. Ratios only.

**13. Serif family: three clips, three incompatible answers.**
v01 and v03 both name **Playfair Display** as closest. v02 explicitly says "NOT a high-contrast display face like Playfair" and proposes Source Serif 4/Spectral. v04's critic measured x-height/cap = 0.66–0.67 and used it to **rule out Playfair (0.739), Lora (0.739), Libre Baskerville (0.754), Merriweather, Noto Serif** — pointing at the Garamond/Crimson/Times class. If these are all the same site, at least two passes are wrong. Nobody has a font-file-level answer, and none is obtainable from video.

**14. Date/clock disagreement.** v01, v02, v06 read 9/15/**2026**; v05 reads 9/1[3|5]/**2025**. The About page's hard-dated content ("At a glance — September 2026", "Since August 27, 2026", Renesas "2024–2026") rests on that clock being right. Chat metadata (21 Sep 2026) supports 2026; v05's read is the outlier.

**15. Copy-level inconsistencies inside his own approved text** — must be carried verbatim or fixed deliberately, never silently normalised: `Sound Source Tracking` (grid) vs `Sound Wave Tracking` (download row) vs `Acoustic wave-based` (body) for one topic; `nondestructive` vs `non-destructive` on one page; `&` vs `/` in the same SHM/NDT title; `PhD` vs `Ph.D.`; en-dash `(2023–2024)` vs spaced em-dash `2026 — PRESENT`; Oxford comma present in the bio, absent in the timeline; data-side topics listed in two different orders (hero vs card 2); `Kaynardag`/`Izmir`/`Istanbul`/`Turkey` all stripped of Turkish diacritics while `Boğaziçi` keeps them. In v07: `multi-layer perception` (sic) vs `Multilayer Perceptron`; body "Figure 11" vs caption "Figure 13"; "and the any setting" (broken phrase).

---

### TIER 3 — what a rebuilder simply cannot know from this evidence

- **No interaction states exist anywhere.** Across 152 frames + 1 still, the cursor never enters a link, button, card or the hamburger. No hover, focus, active, visited, disabled or pressed state was ever captured. Every one must be invented.
- **The hamburger was never opened in any of the six web clips.** In the hamburger-era design the nav contents are unknown. image01's list is the only nav evidence and it is **clipped after "Blog"** — the scrollbar proves items continue below (Publications? CV? Contact?).
- **The top of the sidebar is clipped** — any logo, wordmark or "Waves and Data" branding above the portrait is unseen. Note: the string "Waves and Data"/"wavesanddata" **never appears on any rendered page** in the whole corpus. If the site is to be branded that, the branding does not yet exist.
- **No responsive state, no breakpoint, no mobile behaviour.** His one hard requirement is a permanent left menu; what happens below the breakpoint is undefined. v02's critic proved the hamburger appears at ~1400 CSS px, i.e. the draft's breakpoint is set *above* a normal laptop.
- **No motion language.** Plain native scroll in every clip; no transition, reveal, parallax or easing observable. Anything animated is a new proposal.
- **The v07 document is only ~13 of 40+ pages.** Sections 5–12 (Neural Network Core, Networks for Specific Tasks, Reinforcement Learning, Wrap-Up, Evaluating Performance, Responsible ML, Glossary, How to Learn ML) were never filmed. Figures 1, 2, 5, 10, 11, 12 are referenced but never shown. Sub-sections 3.1, 3.5, 4.3 skipped; the headings for 3.4, 4.1, 4.2, 4.4 were **inferred, never seen on screen**. The domain table's header row and at least one domain block (fraud/churn/readmission) scrolled past above the frame.
- **v07 contains at least one external hyperlink** (the StatQuest YouTube reference in the blurred v07_017) whose target URL is unrecoverable.
- **Content column geometry is unrecoverable from image01** — every content line is cut on the left by the photo frame.

**Frames that returned little or nothing:** v01_008, v01_012 (unreadable smear); v03_006–008 (continuous scroll, not stops); v04 has only 9 frames for 4.6 s and the hamburger is clipped by the camera in **all nine**; v07_017–021 badly motion-blurred — and that is exactly where §1.1, §1.2 and the only hyperlink live; v06_009 mid-flick ghosting.

---

### TIER 4 — artefacts to demand from the professor, in order of value

1. **Access to the builder project** — Lovable (or Claude) project `34000a66-3304-4430-a914-5c4a1656cce7`, chat `9994de28-52ce-4af7-8d44-37ec65de63bb`, project name **"Korkut's Research Hub"**, chat title **"Build webpage with provided files"**. He said "Linkler yok" — but the project is in *his* account. Ask him to open it and hit Share, or export. This single item makes Tiers 1–3 above largely moot: real HTML/CSS, real hex values, real font stacks, the real nav list, the real footer, the figure assets at source resolution.
2. **The PPT** he promised ("Ppt yi birazdan atacagim") — it is the *origin* of the design Lovable converted. Not received.
3. **The Dropbox link** ("aksama dogru atacaim") — updated Word files + figures for all sections. Not received. Without it we have exactly one source doc on disk (`content/dynamical-behavior/source.docx`).
4. **`Machine Learning - The Complete Picture and Guide_5.docx`** specifically — 9,246 words, we hold only blurry frames of a third of it.
5. **The Signal Processing / System Identification / Estimation / Optimization** document (the Wix version is 3,321 words and he says Wix content is outdated).
6. **Which draft is "bu taslak"**, and whether the left menu is description or instruction (item 3 above).
7. **CV file** — the About page's primary button is "Download CV (coming soon)" with an explicit placeholder caption.
8. **Profile URLs**: Google Scholar, ResearchGate, ORCID (LinkedIn is in `PROJECT.md`). All three render as "link coming soon" in two separate pages.
9. **Which email to publish.** Three are in play: `korkut.kaynardag@gmail.com` (printed in the ML doc's Disclaimer), `korkutkaynardag@iyte.edu.tr` (PROJECT.md), `korkut.kaynardag@utexas.edu` (his Wix login). The Contact page says "[Email address coming soon]".
10. **Office details** — "[Office details coming soon]" on the Contact page; PROJECT.md has C220 / 0232 750 6813. Confirm what may go public.
11. **Evidence for the "At a glance" numbers** — 12 published articles, **2 patents (1 granted, 1 pending)**, 8 awards. The patents appear nowhere else in any source. The old Wix CV lists 12 articles, 6 proceedings, 4 talks. Needs a real list, and a decision on whether to hardcode numbers that silently go stale.
12. **Diacritics decision** — `Kaynardag`/`Kaynardağ`, `Izmir`/`İzmir`, `Istanbul`/`İstanbul`, `Turkey`/`Türkiye`. PROJECT.md notes both surname spellings matter for Scholar indexing, so this is not cosmetic.
13. **Headshot at source resolution** — two different crops exist (landscape brick-wall in v01/v02, circular in image01). Possibly already in `reference/wix-media`; verify before asking.
14. **Gallery intent** — the sidebar has a "Gallery" item and the /research copy promises the documents live "under the Gallery section", while the old Wix gallery is 27 photos in 14 sets. Those are two different things sharing one name.
15. **Blog originals** — 8 posts exist only as Word screenshots (`content/blog/*/page-NN.png`, 121–263 real words each). If the source Word files still exist, ask; OCR is the fallback he already endorsed.
16. **English-only?** Unanswered in the chat.
17. **Footer content** — nothing in the corpus establishes it exists, let alone what goes in it.

**Recoverable in-house, do not waste a question on:** clip→file mapping (done above), the 103 Wix media originals (done), old page HTML (done), blog text via OCR, domain facts (RDAP: registrar Wix.com Ltd., paid to 13 Dec 2027, locked, NS at WIXDNS).

---

### Blunt summary

The corpus proves the *content* exists and is his, and proves a consistent restraint (ivory paper, serif headings over sans body, hairlines, no cards, no shadows, no motion). It does **not** establish a single approved page design, a single accent, a single font, a single viewport, a footer, any interaction state, any responsive behaviour, or — most damagingly — whether the left sidebar he demanded is a thing he has already seen and approved, or a thing that has never been built. Roughly 70% of the measured numbers in the seven first passes were overturned by their own critics, and several of the critics overturn each other. Building from this evidence alone means guessing on the two decisions that matter most: the shell, and the long-document page that is 90% of the site's actual content. Obtain item 1 (builder project access) and items 2–3 (PPT + Dropbox) before writing any layout code.