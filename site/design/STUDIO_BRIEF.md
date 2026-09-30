# Wix Studio build brief (2026-09-23)

## Goal
Rebuild the new static design (site/, built with `python site/build.py --out <dir>`) inside the
Wix Studio site **wavesanddata-studio**, metaSiteId `e4242161-3b8c-4fd2-9763-7c93b4063a15`
(created from the Studio blank template, `studio: true`, **unpublished**). Use native Studio
elements so the professor can edit text and images in the Studio editor, and CMS-bound pages
where content repeats (Documents, Topics, Gallery photos, Blog), so a new CMS row becomes a new
page or card without editor work.

Editor URL (opens in the user's Chrome, signed in):
https://manage.wix.com/editor/e4242161-3b8c-4fd2-9763-7c93b4063a15

## Design sources (binding)
- site/design/DESIGN_BRIEF.md (palette, type scale, measure, hover vocabulary), PALETTE.css
- site/parts/*.md (section specs) and site/parts/*.py (the CSS/JS each section ships)
- site/build.py: NAV, DOCS table, page templates, verbatim professor constants PROF_*
- The built static site (site/dist or a fresh `--out` build) is the visual reference.
  Serve it locally and compare at 1280 px and 390 px.

Pages: Home, About Me, My Research Areas, the three topic pages (Vibrations and Waves; Signal
Processing, System Identification, Estimation, Optimization; Machine Learning), Documents
(index + one dynamic item page per CMS row), Gallery (photos), Blog (Wix Blog pages, styled),
Contact. Left navy sidebar on every page (name, nav, current page in the warm accent,
collapsible on desktop, drawer on mobile).

## Rules
- Professor's sentences verbatim (PROF_* constants). No em dashes in any text we write.
- Only email anywhere: korkutkaynardag@iyte.edu.tr.
- Never publish the site, never connect a domain, never touch any other site (the live site
  36a33e18-0863-4d42-8bbd-70c189d86351 and the duplicate c810e33e-579e-45f2-96a2-02d6922a0fce
  are off limits). No purchases, upgrades, plan changes, terms or consent prompts: if a dialog
  asks for any of these, close it and report.
- The editor autosaves. Take a `DS.history.captureCheckpoint()` before each bulk change so a
  bad import can be reverted. If the document looks corrupted, stop and report.

## Mechanics found on 2026-09-23 (the editor's own document API)
In the editor tab (claude-in-chrome javascript_tool):

    const e = window.repluggableAppDebug.utils.apis()
      .find(a => a.key && a.key.name === 'Document Services API');
    const DS = typeof e.impl === 'function' ? e.impl() : e.impl;

- `DS.importExport.pages.jsx.export(pageRef)` returns
  `{version:'0.41.0', structure:{type:'jsx',content}, style:{type:'css',content},
  layout:{type:'css',content}, unmapped:{type:'json',content}}`.
  Layout is real CSS: `--spx(n)` scaled units (ref width 1280), grid containers, and
  `@scope (#pageId) { @media (max-width:1000px) … (max-width:750px) … }` per breakpoint.
- `DS.importExport.global.jsx.export()` returns `{components:[{name,path:'global-components',
  export}], menus, themes}`: header, footer and hamburger MenuContainer are global components
  referenced from each page as `<HeaderSection_x id=… sharedCompId=…/>` RefComponents.
- `DS.importExport.pages.jsx.add(bundle)` WORKS: it returned `{id:'usgjt',type:'DESKTOP'}`,
  the page exists (`DS.pages.getPagesList(true,true)`, `DS.pages.doesPageExist`) and was added
  to the main menu. `DS.pages.getPagesData()` looked stale right after. `.replace()` exists
  (signature unverified). Also `pages.wml/core/eml`, `components.jsx/wml` (add/replace/export).
- Other namespaces: `components.add/serialize/data/properties/cssStyle(update,get,customCss)/
  stylable/responsiveLayout`, `pages.add/remove/navigateTo`, `routers` (dynamic pages),
  `mainMenu`, `menu`, `theme.colors/fonts/textThemes`, `fonts`, `wixCode.provision()` (Velo is
  NOT provisioned yet) and `wixCode.fileSystem` (readFile/writeFile), `history`.
- Rich text: `<WRichText data={{"type":"StyledText","text":"<p class=\"font_7\">…</p>",
  "stylesMapId":"CK_EDITOR_PARAGRAPH_STYLES","linkList":[…]}} props={{"type":
  "WRichTextProperties","packed":true}}/>`.
- Do NOT call `DS.waitForChangesAppliedAsync()`: it hung for 45 s and timed out the tab.
- Tool limits: javascript_tool truncates long strings (about 1000 chars) and arrays over 100
  items; the extension replaces JWT-looking dotted strings and base64-looking strings with
  "[BLOCKED: …]". Stash big values on `window.__x`, replace "." with "·" before returning,
  and read in ≤900-char chunks (≤100 per call). To move a big local file INTO the page, inject
  an `<input type=file>` and use the claude-in-chrome file_upload tool, or send chunks.
- A probe page "Studio Test" (id usgjt, uri studio-test) exists from the test. Remove it.

## Content
A separate agent is creating the CMS collections, media and blog posts in this same site via
REST. It writes build/wix/studio/REPORT.md (collection ids, field keys and types). Build the
shell and static pages first; bind datasets, repeaters and dynamic pages once that file exists.

## Method
1. Learn the format by export: add one sample of each element the design needs to a scratch
   page (text, image, button, container/stack, repeater, dataset, rich content viewer, vertical
   menu, gallery), export JSX, save under build/studio/samples/.
2. Write tools/studio_build.py that emits one bundle per page (build/studio/pages/*.json) from
   the static site's content and the design tokens.
3. Import, screenshot at 1280 and 390 in editor preview, compare with the static site, fix,
   repeat. Keep a log in build/studio/LOG.md.
