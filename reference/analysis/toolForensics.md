## 1. VERDICT — the builder is **Lovable (lovable.dev)**. Certain.

I re-opened the frames myself and read the omnibox at 5–7× rather than relying on the pass/critic summaries. Frame `v02_006.jpg` renders the host in full:

**`https://lovable.dev/chats/9994de28-52ce-4af7-8d44-37ec65de63bb?artifact=project%3A34000a66-3304-4430-a914-5c4a1656cce7`**

Corroborating, all read directly off the pixels:
- Chat composer placeholder `…able anything…` → **"Ask Lovable anything…"** (v02_006 rail).
- Suggestion pills **`…o free link`** + **`Plan custom-dom[ain]`** — Lovable's exact free-`.lovable.app`-link vs paid-custom-domain fork.
- Toolbar triad **Share · ⚡Upgrade · Publish** with a globe project pill **"Korkut's Research Hub"** and an editable route field.
- Browser is **Microsoft Edge**, dark theme, tabs "Zimbra Inbox" + "Build webpage with provided files".

**Correction to the record:** the v03, v06 and image01 passes identified this as *claude.ai Artifacts*. That was an inference from the `?artifact=project%3A…` query parameter — **in those clips the host is never on screen** (I verified: in `v06_002` the omnibox text begins mid-UUID at `52ce-4af7-…`, the scheme/host is off the left edge). Lovable uses the same `?artifact=project:<uuid>` parameter. It is Wix-free, Claude-free, v0-free: one tool, one project, all seven clips + the still.

## 2. Reconstructed address, character by character

```
https://lovable.dev/chats/9994de28-52ce-4af7-8d44-37ec65de63bb
       ?artifact=project%3A34000a66-3304-4430-a914-5c4a1656cce7
```

| Segment | Value | Confidence | Evidence |
|---|---|---|---|
| scheme + host + path | `https://lovable.dev/chats/` | **certain** | v02_003–007; I read v02_006 directly |
| chat uuid g1 | `9994de28` | `de28` **certain**; `9994` **probable** | `4de28` also in image01 (sharp still); leading `999` legible only in v02 (v02_003 blurs it to `l994da28`) |
| g2 | `52ce` | **certain** | v02, v03, v05, v06, image01 |
| g3 | `4af7` | **certain** | crisp in v06_002 and v02_006; v03's `4a17` is a misread — reject |
| g4 | `8d44` | **certain** | every clip |
| g5 | `37ec65de63bb` | **certain** | v02, v03, v06, image01; v05's `…da63bb` is moire |
| query key | `?artifact=project%3A` (= `project:`) | **certain** | v02, v03, v06, image01 |
| project uuid | `34000a66-3304-4430-a914-5c4a1656cce7` | **certain** | read char-by-char in v02_006 and v06_002 by me; v05's `5c4b1856ce87` tail is a misread — reject |

Other identifiers, all certain: project display name **`Korkut's Research Hub`**; chat/conversation title **`Build webpage with provided files`** (tab title + rail header, truncated variants only). No `.lovable.app` subdomain ever appears — do **not** guess `korkuts-research-hub.lovable.app`.

Routes exposed by the builder's own route field / page selector: **`Homepage`**, **`/about`**, **`/research`**, **`/vibrations-waves`**, **`/contact`**. The sidebar still (image01) adds nav entries implying `gallery`, `signal-processing…`, `machine-learning`, `blog`, plus unknown items below the fold. It is genuinely multi-route, not an anchor-scroll page.

## 3. Published / shareable status — almost certainly **NOT published**

- Lovable's publish button reads **"Publish"** before first deploy and changes to **"Publish changes"** once a project is live (per Lovable's own docs). Every frame across all seven clips reads plain **"Publish"**.
- The ⚡**Upgrade** pill is present throughout → **free plan**. Custom domains (wavesanddata.com) are a paid feature, which is exactly why his last chat message is *"ok before going forward, can you publish this free on 🔗 wavesanddata.com…"* and why Lovable answered with the `…free link` / `Plan custom-domain` fork.
- v02 and v05 show the **same rail state** (same message, same pills, same "Enable notifications" banner) → all clips are one continuous session, ~10:05–10:09 AM, 15 Sep 2026, and that publish question was still unanswered when he filmed.

Consequence: **there is no public URL to scrape.** The source exists only inside his Lovable account.

## 4. Exactly what to ask him — in Lovable's own UI wording

Best → worst, all verified against docs.lovable.dev:

1. **Give us the code via GitHub** (cleanest, gives real files + history):
 *Project settings → Git → GitHub → **Connect*** (or the chat actions menu: **Project → GitHub**). Lovable creates a **private** repo and two-way-syncs it. Then he adds us on GitHub as a repo collaborator. Tell him explicitly: **do not rename, transfer or delete that repo afterwards** — it breaks Lovable's sync.
2. **Add us inside Lovable as an editor:**
 **Share** button in the top bar → **Invite people** → **Add people** (email) → access level **Editor** → **Invite**.
3. **View-only, fastest, no account needed by him beyond his own:**
 **Share** → **Share preview** → **Create new preview link** → **Create preview link**. Gives anonymous view-only access to the current in-progress app — useful for pixel-matching, useless for source.
4. **Direct download — likely blocked on his plan:** *Project settings → Git → **Download codebase*** (also a **Download codebase** button at the bottom of the Code editor file-tree sidebar). Documented as **paid plans only**, and he is on free. Mention it last.
5. Also ask for **the files he originally uploaded to that chat** — the chat is literally named *"Build webpage with provided files"*, so his source .docx/figures are attached in that conversation.

Give him the direct link to paste-and-open: `https://lovable.dev/chats/9994de28-52ce-4af7-8d44-37ec65de63bb`

## 5. What the Word clip (v07) reveals about his authoring setup

- **Microsoft Word for Windows, Microsoft 365 desktop** (Aptos-era build), Windows 11. **AutoSave = Off** — the file on disk may lag what he last edited on screen.
- File: **`Machine Learning - The Complete Picture and Guide_5`** — manual `_N` versioning, i.e. at least 5 hand-saved revisions. Ask for the newest, by name.
- **Add-ins installed:** `MathType Add-in` tab, `Acrobat` tab (Adobe PDFMaker), and Home-tab groups `Adobe Acrobat`, `Voice`, `Editor`, `Add-ins`, `MathType`, **`Claude`** (Claude for Office) — the last confirms his "I prepared everything with Claude" workflow runs inside Word.
- Status bar: **9,246 words**, English (United States), Text Predictions On. TOC = **12 numbered sections, 40+ pages**.
- **Page setup (Layout tab, read off the ribbon):** single column, Indent Left/Right `0"`, Spacing **Before 10 pt / After 2 pt**, margins ≈0.69–0.75in (Word "Moderate", *not* 1in), body **fully justified** at a ~110–120-character measure.
- He was parked on the **Layout tab with Selection Pane hovered** through the whole scroll → he has been hand-arranging floating/anchored objects. Figure anchors are fragile; trust caption numbers, not object order.
- **Callouts are single-cell Word TABLES**, not shaded paragraphs — the four-arrow table move handle is visible at the box corner in v07_020. At least two variants exist (heavy oxblood left bar + blush fill; and a thin full outline).
- **Figures are three different species:** (a) Word tables styled as diagrams (Fig 3 pipeline); (b) grouped Word shapes + connectors (Fig 7, the Random-Forest voting figure); (c) raster chart exports, matplotlib-flavoured (Figs 4, 6, 8, 9).
- **MathType is installed but this document has no equations** (it says so explicitly). His other topic documents — Vibrations and Waves, Signal Processing — very likely do.
- One emoji renders as a **missing-glyph box**; one real inline **hyperlink** (StatQuest YouTube) exists despite the first pass claiming no URLs; his gmail is printed in the Disclaimer callout.

## 6. What that implies for the docx → web pipeline

1. **Demand `.docx`, never PDF.** He has the Acrobat add-in and will reach for "Save as PDF"; that destroys headings, tables and alt-text.
2. **Prefer `mammoth` with a custom style map over plain pandoc** for the prose: it preserves run-in `<strong>` lead-ins ("Real-world:", "Use it when:") and lets you map his heading styles to `h2/h3`. Use `pandoc -f docx --extract-media=./media` alongside it purely to pull embedded rasters.
3. **Check first whether he used real Word styles or direct formatting.** If direct, style mapping is dead and you fall back to structural regex: `^\d+\. ` → `h2`, `^\d+\.\d+ ` → `h3`. This single fact determines how much of the conversion can be automated — verify it in the file before writing any converter.
4. **Shape-based figures will silently vanish.** Both pandoc and mammoth extract only `w:drawing/pic:pic` rasters; grouped DrawingML shapes (Fig 3 / Fig 7 / RF voting) come out as nothing. Redraw those three as **inline SVG** — they are box-and-arrow simple, and SVG makes them theme-aware for the ivory/dark modes. The matplotlib-style rasters (4, 6, 8, 9) are probably ~100 dpi; ask for the original PNGs or the plotting code rather than upscaling.
5. **Detect single-cell tables and emit `<aside class="callout">`, not `<table>`.** Rule: 1 row × 1 cell → callout; first paragraph bold+red → callout heading. Handle the outlined variant and the bold closing-sentence pattern.
6. **Real tables** (3-col, bulleted lists per cell) must collapse to stacked blocks on narrow screens, and **justification must be stripped inside cells** — the 3.2 table rivers badly at source.
7. **MathType, for the other documents:** convert *before* export — MathType ribbon → **Convert Equations…** → to Word native (OMML)/MathML. Pandoc turns OMML into MathML/LaTeX cleanly; left as MathType OLE objects they degrade to EMF images or are dropped. Then render with KaTeX. This doc needs none of it.
8. **Rebuild numbering and cross-references.** "Section 5.3", "Section 9.4", "Figure 7" appear constantly and are the single biggest thing a site gains over the .docx — make them anchors. Note the source defect: body says *Figure 11*, caption says *Figure 13*; Figures 2, 5 and 12 are referenced but never filmed.
9. **Drop print artifacts, keep his voice.** Discard page numbers, repeated table header rows, orphan rows and the half-empty pages (page 11 is nearly blank). Drop full justification; cap the measure at 65–75ch. Keep first-person prose, spaced em dashes, italic "Aha!", and the Claude credit lines — he wrote them deliberately.
10. **Flag, don't silently fix**, his inconsistencies: "multi-layer **perception** (MLP)", "and the any setting", nondestructive vs non-destructive, PhD vs Ph.D., missing Turkish diacritics (Kaynardag / Izmir / Istanbul), "Sound Source Tracking" vs "Sound Wave Tracking", the missing-glyph emoji, and whether `korkut.kaynardag@gmail.com` (personal, not IZTECH) should be public.
11. **The document's palette is the site's palette.** Terracotta H1s, blush callouts with oxblood left rule, peach table headers, crimson chart ink — the same warm system as the approved Lovable draft. One token set serves both; define it once.
12. **The 12-section TOC is the sub-navigation** for the Machine Learning branch of the left sidebar he insists on ("sol kisimda menu olcak hep"), and it satisfies his requirement without inventing structure.

**Forensic crops I generated (kept for re-verification):**
`C:\Users\lenovo\AppData\Local\Temp\claude\C--Users-lenovo-Documents-wavesanddata\0ce76f25-a5ca-426b-88a5-bbb15e6df62c\scratchpad\top006.png`, `url006a.png`, `url006c.png`, `uuid006.png`, `rail006.png`, `rail05.png`, `v06top.png`

Sources: [Lovable · Share a project](https://docs.lovable.dev/features/share-project) · [Lovable · GitHub integration](https://docs.lovable.dev/integrations/github) · [Lovable · Publish](https://docs.lovable.dev/features/publish) · [Lovable · Collaboration](https://docs.lovable.dev/features/collaboration)