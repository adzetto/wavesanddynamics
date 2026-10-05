# -*- coding: utf-8 -*-
"""theme - the design tokens, the type system and the navigation column.

Renders no markup. It is loaded first (build.py: `theme = part("theme")`), so its
CSS is the first thing in parts.css and therefore overrides style.css, which the
page links ahead of it.

Everything here is generated in OKLCH at a pinned hue and clamped into sRGB, then
checked with the WCAG 2.x formula. Every ratio quoted in a comment was computed,
not remembered. See DESIGN_BRIEF.md for the reasoning and the full table.

The fonts are the site's own files: Source Serif 4 (opsz 8..60, weights 400
to 600) and Source Sans 3 (400 and 600), split by script as Google Fonts
splits them, in fonts/, which build.py copies from site/fonts/ with their SIL
Open Font License. They are declared here, and shell() preloads the two latin
files, so no request leaves the site for a font and no visitor's address goes
to a font service (ROUND4_SPEC.md section 7). Georgia and Segoe UI stand in,
sized to them, until they arrive.

Above 1000px the column folds away at the reader's request and stays folded
from page to page (THE FOLD, below); build.py's shell() writes the buttons and
the script that restores the choice before first paint.

The column opens with his portrait over his name (THE COLUMN; ROUND5_SPEC.md
section 1), then six of his rows (build.py's NAV; his six topics are in the
Big Picture row's list), a title each and his sub-line under some. The home page's band sits beside the name block on a
desktop and ends where the column's navy starts (THE MASTHEAD). Its motion
(27 Sep 2026): a row fills out of its rail under the pointer, a hairline
draws round the portrait (THE RING), and the first page of a visit sets
the letterhead in (THE ARRIVAL).
"""

__all__ = ["CSS", "JS", "render"]

from .springs import SPRINGS

CSS = """
/* The column fits one screen, the Big Picture list open or closed, and
   nothing in it changes size when the list opens. Since the professor took
   his six topics out of the column (25 Sep 2026) it holds six rows, and the
   topics live only in that list (parts/bpnav.py). Measured in Chromium with
   the list open, its rows at their full 12px of padding (THE COLUMN,
   below), the last row ends at 697px in a window 721 to 860px tall and at
   768px in a taller one: 71px to spare at 1366x768, 103px at 1280x800, 132px
   at 1440x900. A window 643px tall still holds it all, its rows at 6px. The
   phone drawer at 390x844 ends at 770px. So the rules that hid the topics'
   own rows (:has()) and the ones that shrank the portrait and tightened
   every row while the list was open are gone; the second also moved the
   name block, which the home page's band must meet (--id-h). The portrait
   stays 56px in a short window: portrait() in build.py asks for the 56px
   file there (its sizes), and the rows' padding counts on it. At 108px the
   open column would reach the foot of a 1366x768 window. */
/* his words, linked where they name a place on the site: the link fills with
   the warm wash from the left on hover, as the site's cards do */
.inlink{position:relative;color:var(--link);text-decoration:underline;
  text-decoration-thickness:1px;text-underline-offset:4px;
  background:linear-gradient(var(--wash),var(--wash)) no-repeat left/0% 100%;
  border-radius:3px;padding:0 2px;margin:0 -2px;
  transition:background-size 360ms cubic-bezier(.2,.8,.2,1),color 200ms}
@media (hover:hover){.inlink:hover{background-size:100% 100%;color:var(--accent);
  text-decoration-color:var(--accent)}}
.inlink:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
@media (prefers-reduced-motion:reduce){.inlink{transition:none}}
.rv{opacity:0;transform:translateY(12px);transition:opacity 520ms cubic-bezier(.2,.8,.2,1),transform 620ms cubic-bezier(.2,.8,.2,1)}
.rv.in{opacity:1;transform:none}
/* a block the address points into is where the reader is going: it stands in
   place at once, so the landing is measured from where it will stay */
.rv:has(:target){opacity:1;transform:none;transition:none}
@media print{.rv{opacity:1!important;transform:none!important}}
/* The fonts, from the site's own fonts/ folder: url() resolves against this
   stylesheet, parts.css, at the site's root, so every page, a document's
   too, reads the same files. Each face is split by script as Google Fonts
   splits it, so a page downloads only the files its text touches: most
   pages need the two latin files alone, which shell() preloads; About
   ("Bogazici" with its g-breve) adds the serif's latin-ext, From Bridges to
   Photons (a lambda) its Greek. The Turkish letters latin leaves out (G and
   S with their marks, the dotted capital I) come from a 7 KB cut of the
   serif's latin-ext of their own, for the footer's credit on every page
   ("Yagcioglu"), which had every page fetch the 101 KB file for one g. Each file is variable: the serif carries its
   optical sizes and the weights 400 to 600, the sans its 400 and 600. */
@font-face{font-family:"Source Serif 4";font-style:normal;font-weight:400 600;font-display:swap;
  src:url(fonts/source-serif-4-latin.woff2) format("woff2");
  unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,
    U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:"Source Serif 4";font-style:normal;font-weight:400 600;font-display:swap;
  src:url(fonts/source-serif-4-latin-ext.woff2) format("woff2");
  unicode-range:U+0100-011D,U+0120-012F,U+0132-015D,U+0160-02BA,U+02BD-02C5,U+02C7-02CC,
    U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,
    U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}
@font-face{font-family:"Source Serif 4";font-style:normal;font-weight:400 600;font-display:swap;
  src:url(fonts/source-serif-4-tr.woff2) format("woff2");
  unicode-range:U+011E-011F,U+0130,U+015E-015F}
@font-face{font-family:"Source Serif 4";font-style:normal;font-weight:400 600;font-display:swap;
  src:url(fonts/source-serif-4-greek.woff2) format("woff2");
  unicode-range:U+0370-0377,U+037A-037F,U+0384-038A,U+038C,U+038E-03A1,U+03A3-03FF}
@font-face{font-family:"Source Sans 3";font-style:normal;font-weight:400 600;font-display:swap;
  src:url(fonts/source-sans-3-latin.woff2) format("woff2");
  unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,
    U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:"Source Sans 3";font-style:normal;font-weight:400 600;font-display:swap;
  src:url(fonts/source-sans-3-latin-ext.woff2) format("woff2");
  unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,
    U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,
    U+2C60-2C7F,U+A720-A7FF}

/* Georgia stands in until Source Serif 4 arrives, scaled to its advance so the
   swap does not rewrap the page. Measured in Chromium on a long sample: at 400
   the two are within 1.5%, but Source Serif 4 600 is 0.83 to 0.89 of Georgia
   Bold's width, which put an extra line into headings and bold runs and moved
   the brochure by 0.11 CLS on a phone. It is still Georgia on screen; only its
   size changes, and only while the web font is loading or missing.
   Its vertical metrics are set too, divided by the size adjustment, which
   scales them. Source Serif 4 has an ascent of 1036 and a descent of 335 on
   the thousand (its OS/2 table, which it tells browsers to use) and a cap
   height of 670; Georgia has its own, and without these every line of
   Georgia had a text box of another height and a baseline elsewhere, which
   Chrome counts as a layout shift the moment the web font lands: 0.09 CLS on
   the home page at 1280x800 in Lighthouse, 0.04 with them (measured on a
   cold load; what is left is a line of prose that breaks one word earlier
   in Georgia). Two rules do it. Ascent plus
   descent is the height of a text box, so each face below gives exactly
   Source Serif 4's 1.371em. Ascent minus descent puts the baseline: at 400
   it is Source Serif 4's too, so the prose lands on the same pixel. At 600
   it is 0.547em instead, the value that keeps the cap line where Source
   Serif 4 has it, because Georgia Bold's cap height at 85.6% is 0.593em, not
   0.670: a heading trimmed to its cap line (text-box, in the hero and on
   About) then keeps its height through the swap, and the page under it
   stays put, while a bold run's glyphs sit 0.08em high until the swap.
   At 400 the size is 100.6%, not the long sample's 101.5%: at 101.5% the
   home page's "Myself:" paragraph set "2016-2023)." a line lower in Georgia
   and moved three lines at the swap (0.026 to 0.043 CLS from 1280x800 to
   1350x940). Measured over twelve pages at 1280x800, 1350x940 and 1440x900,
   index stays under 0.01 from 100.3% to 100.8%, About goes to 0.07 at
   100.2%, and index is back at 0.04 at 101%; 100.6% is the middle. */
@font-face{font-family:"Source Serif 4 Fallback";font-style:normal;font-weight:400;
  src:local("Georgia");size-adjust:100.6%;
  ascent-override:102.98%;descent-override:33.3%;line-gap-override:0%}
@font-face{font-family:"Source Serif 4 Fallback";font-style:normal;font-weight:600 700;
  src:local("Georgia Bold"),local("Georgia-Bold");size-adjust:85.6%;
  ascent-override:112.05%;descent-override:48.12%;line-gap-override:0%}
/* Segoe UI stands in for Source Sans 3 the same way: 94% of its size is the
   same advance (0.9397 at 400 and 0.9395 at 600, on the column's own labels,
   at every size from 13 to 40px), so the twelve rows set on the same lines
   in both faces, and Source Sans 3's ascent and descent (1024 and 400). A
   system without Segoe UI skips it for the next font in --sans. */
@font-face{font-family:"Source Sans 3 Fallback";font-style:normal;font-weight:400;
  src:local("Segoe UI"),local("SegoeUI");size-adjust:94%;
  ascent-override:108.94%;descent-override:42.55%;line-gap-override:0%}
@font-face{font-family:"Source Sans 3 Fallback";font-style:normal;font-weight:600;
  src:local("Segoe UI Semibold"),local("SegoeUI-Semibold");size-adjust:94%;
  ascent-override:108.94%;descent-override:42.55%;line-gap-override:0%}

/* ==========================================================================
   TOKENS - light
   Hues are pinned: paper and ink at OKLCH H 75-80, the column at H 248 (inside
   the 238-255 band Oxford, Yale, Nature and Distill occupy; the old #104862 sat
   at 233.8, outside it on the cyan side), the accent at H 52.
   ========================================================================== */
:root{
  /* --- paper. Warm, C <= 0.010: above that it reads beige, not paper. ------ */
  --page:#FBF9F6;          /* oklch(.983 .0045 78) */
  --surface:#F6F3EF;       /* oklch(.965 .0062 75) */
  --card:#F2EFE9;          /* oklch(.953 .0086 85)  muted on it 4.67:1, was 4.10 */
  --wash:#FEEBDB;          /* oklch(.951 .0297 63)  body on it 7.00:1 */
  --rule:#E5E1DB;          /* hairline separator, 1.24:1, decorative */
  --line:#D7D2CA;          /* surface border, 1.43:1, decorative */
  --line-strong:#8A857C;   /* 3.49:1 on page, 3.20:1 on card. Use wherever a
                              border is the ONLY affordance: inputs, ghost button */
  --soft:var(--surface);

  /* --- ink, warm neutral to match the paper ------------------------------- */
  --ink:#27221C;           /* 15.00:1 on page */
  --body:#544F48;          /*  7.72:1 on page,  7.07:1 on card */
  --muted:#6F6A64;         /*  5.10:1 on page,  4.67:1 on card, 4.84:1 on surface */

  /* --- the column. Blue means place. ------------------------------------- */
  --nav:#043052;           /* oklch(.300 .076 248)  white on it 13.55:1 (was 9.88) */
  --nav-hover:#104169;     /* LIGHTER than --nav. The old #0C3A50 was darker, so a
                              hovered row receded. White on it 10.59:1 */
  --nav-2:var(--nav-hover);/* legacy name, repointed: its only live consumer is the
                              sidebar hover, which must lighten */
  --nav-press:#002341;     /* white 15.95:1 */
  --nav-deep:#001C35;      /* white 17.25:1 */
  --nav-ink:#FFFFFF;       /* 13.55:1 on --nav */
  --nav-mute:#C3CDD5;      /*  8.40:1 on --nav, for secondary text in the column */
  --nav-rule:rgba(255,255,255,.14);  /* ONE group separator, never per-row */

  /* --- the accent. Warm means action, and "you are here". ----------------- */
  /* Two values, because one cannot do both jobs (Radix step 11 vs step 9). */
  --accent:#A5510B;        /* ink on paper: 5.28:1 on page, 4.84:1 on card.
                              This is the only warm allowed to carry text or fill
                              a control on the paper. White on it 5.55:1 */
  --accent-2:#E7813B;      /* mark on the dark column: 4.90:1 on --nav (the old
                              #80350E was 1.14:1, an outright WCAG 1.4.1 failure).
                              Never text on paper: it is 2.4:1 there */
  --accent-on-nav:var(--accent-2);   /* say what you mean at the call site */
  --accent-hover:#904607;  /* white 6.85:1 */
  --accent-press:#7B3D0C;  /* white 8.35:1 */
  --active:var(--accent);  /* legacy name. Numerals, timeline dates, small marks.
                              It is NOT the active-nav fill any more: see .nav .on */
  --btn-fg:#FFFFFF;        /* flips to dark text in dark mode */

  /* --- links and focus ---------------------------------------------------- */
  --link:#095A94;          /* 6.89:1 on page. No longer the same hex as --nav */
  --link-hover:#004170;    /* 10.04:1 */
  --focus:var(--nav);      /* 12.89:1 on page, 11.81:1 on card. Inside the navy
                              column the ring is #fff instead, at 13.55:1 */

  /* --- type --------------------------------------------------------------- */
  --serif:"Source Serif 4","Source Serif 4 Fallback",Georgia,Cambria,"Times New Roman",serif;
  --sans:"Source Sans 3","Source Sans 3 Fallback","Segoe UI",system-ui,-apple-system,sans-serif;
  --lh:1.50;               /* leading ladder, widened below */
  --measure:608px;         /* 70.5 characters, measured in Chromium at 19px SS4.
                              Never use ch: it is the width of the digit zero */
  --measure-wide:720px;    /* lists, tables, timelines: not prose */
  --measure-fig:924px;     /* figures breaking out of the prose column */
  --measure-doc:672px;     /* a document page's one column: text, figures, tables
                              and captions share it. 75.6 characters a line at
                              19px (measured in Chromium on the ML guide), and
                              exactly that guide's own Word column (672px) */

  /* --- surfaces, motion --------------------------------------------------- */
  --side:240px;            /* 16.7% of 1440px, which is the ratio of the column in
                              his own deck (2.23in of 13.33in). Was 264px = 18.3% */
  --id-h:262px;            /* the identity block over the column: his portrait,
                              name, post and affiliation (217.55px of content),
                              191px in a window 860px tall or less. The home
                              page's band beside it is at least this tall, so
                              the band ends where the column's navy starts */
  --pic:108px;              /* his portrait at the head of the block, 56px in a
                              short window */
  --fold-top:36px;         /* the fold buttons, centred on the portrait */
  --r-sm:8px; --r-md:8px; --r-lg:8px; --r-pill:999px;   /* two radii, not five */
  --sh-1:0 1px 2px rgba(39,34,28,.04);
  --sh-2:0 1px 2px rgba(39,34,28,.04), 0 8px 24px rgba(39,34,28,.06);
  --sh-3:0 2px 4px rgba(39,34,28,.05), 0 16px 40px rgba(39,34,28,.08);
  --ease:cubic-bezier(.2,.8,.2,1);
  --ease-in-out:cubic-bezier(.4,0,.2,1);
  --ease-state:cubic-bezier(.2,0,.38,.9);   /* Carbon productive standard */
  --t-quick:120ms; --t-fast:160ms; --t-mid:240ms; --t-slow:420ms;
  --t-draw:360ms;          /* a line or a fill drawing itself across a card or a
                              row: a topic card's bloom and icon acts, a career
                              stretch. Leaving always takes a shorter token */
  /* Things that travel move on Motion's springs (springs.py, generated by
     tools/motion_springs.mjs from motion.dev's spring(), bounce 0): each
     --spring-<t> is a whole transition, "<settle> linear(...)", standing in
     for "var(--t-<t>) var(--ease)" on a transform, a dash offset or a clip.
     The spring is where it is going at the token's time and has settled by
     the longer one. Colour and opacity keep --ease-state and --ease: a
     spring means nothing for a colour. A margin keeps its curve too: it
     moves the layout, and a spring would only lengthen that. */
  /*SPRINGS*/
}

/* the leading ladder: the wider the column, the more leading it needs */
@media (min-width:650px){ :root{ --lh:1.55 } }
@media (min-width:1200px){ :root{ --lh:1.60 } }

/* Between pages (a view transition across documents, where the browser has
   one): the column and the phone's bar stay where they are, so the site's
   frame never blinks; the page's own column leaves at once and the next one
   settles in on Motion's spring. A reader who asks for less motion gets the
   plain page load. */
@view-transition{navigation:auto}
.side{view-transition-name:side}
.bar{view-transition-name:bar}
::view-transition-old(root){animation:page-out 110ms var(--ease-state) both}
::view-transition-new(root){animation:page-in var(--spring-mid) both}
@keyframes page-out{to{opacity:0}}
@keyframes page-in{from{opacity:0;transform:translateY(8px)}}
@media (prefers-reduced-motion:reduce){
  @view-transition{navigation:none}
}

/* ==========================================================================
   TOKENS - dark
   ========================================================================== */
:root:not([data-theme="light"]){ @media (prefers-color-scheme: dark){
  --page:#13110F; --surface:#1E1B18; --card:#272420; --wash:#322218;
  --rule:#322E2A; --line:#423E38; --line-strong:#7B756E; --soft:var(--surface);
  --ink:#EBE7E2; --body:#C1BDB7; --muted:#928E88;
  --nav:#12304A; --nav-hover:#1D4161; --nav-2:var(--nav-hover);
  --nav-press:#0B243A; --nav-deep:#081C2F;
  --nav-ink:#FFFFFF; --nav-mute:#C6CDD4; --nav-rule:rgba(255,255,255,.16);
  --accent:#F09458; --accent-2:#FDA670; --accent-on-nav:var(--accent-2);
  --accent-hover:#FFA971; --accent-press:#DA8249; --active:var(--accent);
  --btn-fg:#13110F;        /* white on an amber this light is 3.3:1 and fails */
  --link:#69A5DE; --link-hover:#90C1F1;   /* flips light, Carbon blue 60 -> 40 */
  --focus:var(--link);     /* 7.21:1 on page. --nav would be 1.21:1 here */
  --sh-1:0 1px 2px rgba(0,0,0,.35);
  --sh-2:0 2px 4px rgba(0,0,0,.30), 0 10px 28px rgba(0,0,0,.40);
  --sh-3:0 3px 6px rgba(0,0,0,.35), 0 18px 44px rgba(0,0,0,.48);
}}
:root[data-theme="dark"]{
  --page:#13110F; --surface:#1E1B18; --card:#272420; --wash:#322218;
  --rule:#322E2A; --line:#423E38; --line-strong:#7B756E; --soft:var(--surface);
  --ink:#EBE7E2; --body:#C1BDB7; --muted:#928E88;
  --nav:#12304A; --nav-hover:#1D4161; --nav-2:var(--nav-hover);
  --nav-press:#0B243A; --nav-deep:#081C2F;
  --nav-ink:#FFFFFF; --nav-mute:#C6CDD4; --nav-rule:rgba(255,255,255,.16);
  --accent:#F09458; --accent-2:#FDA670; --accent-on-nav:var(--accent-2);
  --accent-hover:#FFA971; --accent-press:#DA8249; --active:var(--accent);
  --btn-fg:#13110F;
  --link:#69A5DE; --link-hover:#90C1F1;
  --focus:var(--link);
  --sh-1:0 1px 2px rgba(0,0,0,.35);
  --sh-2:0 2px 4px rgba(0,0,0,.30), 0 10px 28px rgba(0,0,0,.40);
  --sh-3:0 3px 6px rgba(0,0,0,.35), 0 18px 44px rgba(0,0,0,.48);
}

/* ==========================================================================
   TYPE
   Serif reads, sans is furniture. 19px Source Serif 4 has a 9.03px x-height
   against 16.5px Inter's 9.01px, so this is not an increase in apparent size.
   ========================================================================== */
body{
  font-family:var(--serif);
  font-size:19px;
  line-height:var(--lh);
  font-optical-sizing:auto;          /* opsz 8..60 stays live at one weight */
  font-variant-numeric:oldstyle-nums proportional-nums;
  -webkit-font-smoothing:auto;       /* antialiased thins 19px serif prose */
  text-rendering:optimizeLegibility;
}
p,li,blockquote{text-wrap:pretty}
.col,.doc,.lede,.introlist{overflow-wrap:break-word}

h1{font:600 clamp(32px,3.4vw,40px)/1.12 var(--serif);letter-spacing:-.014em;
  color:var(--ink);margin:0 0 18px;text-wrap:balance}
h2{font:600 28px/1.22 var(--serif);letter-spacing:-.009em;color:var(--ink);
  margin:47px 0 21px;text-wrap:balance}          /* 2.24:1, was 4.17:1 */
h3{font:600 23px/1.30 var(--serif);letter-spacing:-.004em;color:var(--ink);
  margin:34px 0 14px;text-wrap:balance}          /* was 16.5px: identical to body */
h4{font:600 19px/1.35 var(--serif);color:var(--ink);margin:28px 0 10px;text-wrap:balance}

.lede{font-size:21px;line-height:1.52;letter-spacing:-.004em;color:var(--body)}
th{font:600 12px/1.35 var(--sans);letter-spacing:.09em;text-transform:uppercase;
  color:var(--muted);background:none;border-color:var(--rule)}
td{font-size:15px;line-height:1.45;border-color:var(--rule)}
th,td{font-variant-numeric:lining-nums tabular-nums}
figcaption{font-size:16px;line-height:1.5;color:var(--muted)}
.foot{font-size:14px}
.pending__tag{font-family:var(--sans)}
.stats b,.tl time{font-variant-numeric:lining-nums proportional-nums}
.tl time{font-family:var(--sans);font-size:14px;letter-spacing:.01em}

/* a superscript or subscript never opens its line (the documents' formulas) */
sup,sub{line-height:0}

/* No italic is loaded: Source Serif 4 italic 400 is 92.1 KB, more than the whole
   roman payload. Faux-oblique on a transitional serif is worse than none. */
.soon,.dl.off,.find em,.doc .ink-m{font-style:normal;color:var(--muted)}

/* ==========================================================================
   MEASURE
   Every ch width is deleted. `ch` is the advance of the digit zero, so
   .col{max-width:72ch} rendered at 749px = 101.7 characters (measured in
   Chromium), over WCAG 2.2 SC 1.4.8's cap of 80.
   ========================================================================== */
.col,.lede,.introlist,.pending,.toc{max-width:var(--measure)}
.rows,.tl,.doc .docrule,figure,.callout{max-width:var(--measure-wide)}
.stats span{max-width:200px}

/* ==========================================================================
   THE COLUMN
   One unbroken navy field from the nav block to the foot of the viewport, which
   is his deck. Labels left-aligned on one hard edge at x=20. The current page is
   marked three ways, only one of which is colour (WCAG 1.4.1).
   ========================================================================== */
.side{width:var(--side);background:var(--page);border-right:0}
/* His portrait heads the block (ROUND5_SPEC.md section 1: the home page no
   longer shows it, the column shows it on every page). A real photograph,
   calmly cropped: a square from his headshot, head and shoulders, the head
   about two thirds of the frame and the eyes a little above the middle, in a
   circle, the one shape the brief keeps besides the 8px radius (999px), and
   the shape a person takes in a list of places. It sits on the labels' hard
   edge at x=20, 64px across (56px in a short window): large enough to read as
   his face, not a mark, and a third of the column, so the name under it
   still leads. The edge is a hairline of ink at 10% laid over the photo
   (outline, inset by its own width), so the pale shirt keeps a rim on the
   paper without a coloured ring; --card fills the circle until the file
   arrives. build.py writes it at 1x and 2x (portrait-sq-*.webp). The photo
   itself never moves on hover or focus: the whole block is the link home,
   its name takes the underline and a hairline ring draws itself round the
   photo (THE RING, below). */
.id__pic{display:block;width:var(--pic);height:var(--pic);margin:0 auto 14px;
  box-shadow:0 0 0 3px var(--page),0 0 0 4px color-mix(in oklab,var(--ink) 14%,transparent);
  border-radius:50%;background:var(--card);
  outline:1px solid color-mix(in oklab,var(--ink) 10%,transparent);outline-offset:-1px}
@media (forced-colors:active){.id__pic{outline-color:CanvasText}}
/* The identity is set like a letterhead, in two groups and with no ornament.
   Who he is: the name in the serif at 20px, one step over the 19px prose so
   it leads the column, and his degree and post 5px under it in the sans, in
   --ink. Where he is: department and institute 10px lower, in --muted. The
   gaps make the groups and the colour makes the step between them, so the
   sans stays at one weight and never competes with the name (a 600 post line
   read as a second heading). The amber bar that sat under the name is gone: a
   short rule under a heading is a template's mark. No small caps either:
   neither Source Sans 3 nor Source Serif 4 as Google serves them has smcp
   (checked in Chromium with font-synthesis off), so the browser would fake
   them from shrunken capitals. */
.id{text-align:center;padding:22px 20px 18px;min-height:var(--id-h)}
.id b{font:600 20px/1.2 var(--serif);letter-spacing:-.01em;color:var(--ink);
  text-decoration-line:underline;text-decoration-thickness:1px;
  text-underline-offset:4px;text-decoration-color:transparent;
  transition:text-decoration-color var(--t-quick) var(--ease-state)}
.id__role,.id__org{font:400 13px/1.45 var(--sans);letter-spacing:.006em}
.id__role{margin-top:5px;color:var(--ink)}       /* 15.00:1 */
.id__org{margin-top:10px;color:var(--muted)}     /*  5.10:1 */
/* the whole block is the link home; hovering it underlines the name, as a
   card's title is underlined (DESIGN_BRIEF.md 4) */
@media (hover:hover){
  .id:hover b{text-decoration-color:color-mix(in oklab,currentColor,transparent 62%)}
}
/* the column clips what overflows it, so a ring outside the block would be
   cut on three sides: it sits inside, as the nav rows' ring does */
.id:focus-visible{outline:2px solid var(--focus);outline-offset:-4px}

/* THE RING. The photo's rim already has its track: the pale hairline 3px
   out (the box-shadow above, ink at 14%). Pointing at the block draws a
   navy hairline over that track, from the top of the circle down both
   sides at once until the two ends meet under his chin, above his name: a
   centred letterhead gets a symmetrical stroke. Blue, because the block is
   a place, the way home (DESIGN_BRIEF.md 1.4); it is --focus, the ring
   colour on paper, --nav in light mode (12.89:1) and the light link blue
   in dark mode, where --nav on the page is 1.39:1. On the home page itself
   the block is the page the reader is on, so the ring stands there at
   rest in the warm of "you are here", as the current row's rail does on
   the column. The stroke is a 1px circle shown through a conic mask whose
   angle (--id-arc, registered so it can travel) runs on the draw spring;
   letting go fades it (--t-quick) and folds it away only once unseen, so
   a pointer that comes back finds it drawn. A key takes the drawn ring at
   once. A browser without @property shows the finished ring at once. The
   photo itself never moves. */
@property --id-arc{syntax:"<angle>";inherits:false;initial-value:0deg}
.id{position:relative}
.id::before{content:"";position:absolute;left:50%;top:18px;box-sizing:border-box;
  width:calc(var(--pic) + 8px);height:calc(var(--pic) + 8px);margin-left:calc(var(--pic) / -2 - 4px);
  border:1px solid var(--focus);border-radius:50%;pointer-events:none;opacity:0;
  -webkit-mask:conic-gradient(from calc(var(--id-arc) / -2),var(--ink) var(--id-arc),transparent 0);
  mask:conic-gradient(from calc(var(--id-arc) / -2),var(--ink) var(--id-arc),transparent 0);
  transition:opacity var(--t-quick) var(--ease-state),--id-arc 0s var(--t-quick)}
@media (hover:hover){
  .id:hover::before{--id-arc:360deg;opacity:1;transition:--id-arc var(--spring-draw)}
}
.id:focus-visible::before{--id-arc:360deg;opacity:1;transition:none}
.id[aria-current]::before{--id-arc:360deg;opacity:1;border-color:var(--accent)}  /* 5.28:1 */
@media (forced-colors:active){.id::before{border-color:LinkText}}
/* THE HALO (parts/bpnav.py draws it): the portrait's orb, the dots of a
   sphere round the photo that turn and gather into the pale track as the
   first page of a visit opens, and breathe out of it again, fainter, when
   the pointer or a key comes to the block. Their canvas is made over the
   photo for the motion alone and taken away when it rests; it takes no
   pointer. Blue, --focus, the ring colour on paper; never over his face. */
.id__halo{position:absolute;pointer-events:none}
@media (forced-colors:active){.id__halo{display:none}}

/* THE ARRIVAL. The first page of a visit (head_js() in parts/bpnav.py
   marks <html> data-id-in, once a session, only where the column stands
   open beside the page and motion is welcome) sets the letterhead the way
   a print comes up in the tray: the photo resolves out of a soft blur
   while it grows the last 6% (the slow spring), the fold's button beside
   it fading in with it, then his name, his post and his department
   settle 6px into their lines, 60ms apart, and last the
   warm mark lands on where the reader is: the current row's rail grows
   from its middle, or, on the home page, the warm ring draws round the
   photo. About 0.8s, nothing waits on it (the block is a working link
   throughout) and the page beside it is untouched. Every later page opens
   still: the column is the frame, and a frame does not blink. The script
   takes the mark away once it has played, so nothing replays when the
   window crosses 1000px. */
@media (width > 1000px) and (prefers-reduced-motion:no-preference){
  [data-id-in] .id__pic{animation:id-in 520ms var(--ease) backwards,
    id-grow var(--spring-slow) backwards}
  [data-id-in] .id :where(b,.id__role,.id__org){animation:id-line 420ms var(--ease) backwards,
    id-rise var(--spring-mid) backwards}
  [data-id-in] .id b{animation-delay:160ms}
  [data-id-in] .id .id__role{animation-delay:220ms}
  [data-id-in] .id .id__org{animation-delay:280ms}
  [data-id-in] .fold--hide{animation:id-fade 360ms var(--ease) 120ms backwards}
  [data-id-in] .id[aria-current]::before{animation:id-ring var(--spring-slow) 380ms backwards}
  [data-id-in] .nav .on::before{animation:id-rail var(--spring-mid) 460ms backwards}
}
@keyframes id-in{from{opacity:0;filter:blur(6px)}}
@keyframes id-fade{from{opacity:0}}
@keyframes id-grow{from{transform:scale(.94)}}
@keyframes id-line{from{opacity:0;filter:blur(2px)}}
@keyframes id-rise{from{transform:translateY(6px)}}
@keyframes id-ring{from{--id-arc:0deg}}
@keyframes id-rail{from{transform:scaleY(0)}}

/* The rows, as his slide 1 draws them: a title, and under some of them his
   sub-line in smaller type. The title is the sans at 600 / 15px in white,
   balanced over two lines where it needs them; the sub-line is the sans at
   400 / 13px in --nav-mute (8.40:1 on the column, 6.57:1 on a lit row), at
   most two lines, 2px under its title. Every label starts on one hard edge
   at x=20.

   The eight rows and the Big Picture list, open (the column's longest
   state, with the note under Signal Processing), fit under the identity
   without scrolling in a window tall enough for them, and breathe on a
   taller one, so each row's padding (--pad) is what the window's height
   leaves them once the identity has its share, from 6px up to 12px. Where
   the last row ends is linear in --pad with a kink: the four rows of two
   or three lines grow 2px a pixel of padding, while the one-line rows
   stand on their min-height until the padding outgrows it and then grow
   too. Measured in Chromium on the Big Picture page (5 Oct 2026), the list
   open and --pad forced from 6 to 12px, the last row ends at 827px + 8 x
   --pad below the kink and 746px + 16 x --pad above it with 40px one-line
   rows; in a window 860px tall or less, where the identity is shorter and
   a one-line row 36px, at 740px + 8 x --pad and 675px + 16 x --pad. Both
   lines are in min(), which picks the one in force, with 24px of air left
   under the last row: the open list fits from 900px tall (12px from
   1026px) and, with the shorter identity, from 812 to 860px. In a shorter
   window a page no longer holds the list open (bpnav.py OPEN_FITS): it
   shows the folded line with its warm bead, and opens on the reader's
   click, when the list scrolls inside the column, under the identity,
   which never moves, and its foot fades while there is more below
   (.nav--more). A row is never under 36px, or 44px under a finger. */
.nav li{margin:0}
.nav a{position:relative;text-align:left;
  --pad:clamp(6px,min(calc((100vh - 851px) / 8),calc((100vh - 770px) / 16)),12px);
  padding:var(--pad) 16px calc(var(--pad) + 1px) 20px;
  min-height:40px;display:flex;flex-direction:column;justify-content:center;
  align-items:flex-start;gap:2px;border-bottom:0;
  font:600 15px/1.25 var(--sans);letter-spacing:.006em;color:var(--nav-ink);
  -webkit-font-smoothing:antialiased;        /* white on dark: here it helps */
  transition:background-color var(--t-quick) var(--ease-state)}
.nav__t,.nav__s{display:block;max-width:100%;text-wrap:balance}
.nav__s{font:400 13px/1.3 var(--sans);letter-spacing:.01em;color:var(--nav-mute)}
/* the colon that joins a title to its sub-line in the link's name, unseen */
.nav__sep{position:absolute;width:1px;height:1px;overflow:hidden;
  clip-path:inset(50%);white-space:nowrap}
@media (pointer:coarse){ .nav a{min-height:44px} }
/* A row's states are two layers under its words, so the words never move
   and nothing is laid out again:
   - the fill (::after): the row's lighter navy, halfway to --nav-hover,
     which pours in from the column's edge (a wipe, scaleX from the left);
   - the rail (::before): 3px on the edge, grown from the row's middle.
     Light (--nav-mute) under the pointer, the column's warm mark (4.90:1)
     on the current page: warm stays the colour of "you are here" alone,
     so a hovered row never reads as a second current one.
   Under the pointer the rail and the fill start together, the rail on the
   fast spring and the fill on the mid one, so the rail leads and the row
   fills out of it (160 and 240ms to arrive). Leaving, both fade where they
   stand (--t-quick) and fold back only once unseen: a pointer running down
   the column leaves each row quietly instead of wiping it back, and one
   that returns mid-fade finds the row still filled. The current row keeps
   its own fill and rail at rest; hovering it adds nothing. A key takes
   the end state at once (Emil: no motion on keyboard-initiated actions).
   The fill sits under the words (z-index -1) inside the list, which is
   its own stacking context so the layer stays over the navy. */
.nav{isolation:isolate;--nav-lit:color-mix(in oklab,var(--nav) 50%,var(--nav-hover))}
.nav a::after{content:"";position:absolute;inset:0;z-index:-1;pointer-events:none;
  background:var(--nav-lit);opacity:0;transform:scaleX(0);transform-origin:0 50%;
  transition:opacity var(--t-quick) var(--ease-state),transform 0s var(--t-quick)}
.nav a::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;
  background:var(--nav-mute);opacity:0;transform:scaleY(0);transform-origin:50% 50%;
  transition:opacity var(--t-quick) var(--ease-state),transform 0s var(--t-quick)}
@media (hover:hover){
  .nav a:hover::after{opacity:1;transform:none;transition:transform var(--spring-mid)}
  .nav a:hover::before{opacity:1;transform:none;transition:transform var(--spring-fast)}
}
.nav .on{background:var(--nav-hover)}
.nav a:active,.nav .on:active{background:var(--nav-press)}
.nav .on::before{background:var(--accent-on-nav);opacity:1;transform:none}  /* 4.90:1 */
.nav a:focus-visible{outline:2px solid var(--nav-ink);outline-offset:-4px}
.nav a:focus-visible::before,.nav a:focus-visible::after{opacity:1;transform:none;transition:none}
@media (forced-colors:active){.nav a::before{background:Highlight}.nav a::after{display:none}}
/* the separators, above the row that opens a group (build.py's NAV marks it
   .grp): {About Me, My Research Areas, Gallery}, {the Big Picture and its
   list}, {Blog, Contact} */
.nav .grp>a{box-shadow:inset 0 1px 0 var(--nav-rule)}
/* A window 860px tall or less (1280x800, a laptop): the portrait is 56px and
   the identity 27px shorter, 190.55px of content, which --id-h rounds up to
   191px so the home page's band meets the navy on the pixel, and a one-line
   row may stand at 36px. */
@media (max-height:860px){
  :root{--id-h:191px;--pic:56px;--fold-top:25px}
  .id{padding-top:17px;padding-bottom:12px}
  .id::before{top:13px}          /* the ring's track, 4px out from the photo */
  .id__pic{margin-bottom:12px}
  .id__org{margin-top:8px}
  .nav a{min-height:36px;
    --pad:clamp(6px,min(calc((100vh - 764px) / 8),calc((100vh - 699px) / 16)),12px)}
}
@media (max-height:860px) and (pointer:coarse){ .nav a{min-height:44px} }
/* When the list is longer than the column (a short window, or a list opened
   inside it), its foot fades into the navy while there is more below: the cue
   that it scrolls, where a thin scrollbar alone was easy to miss. The
   shell's script sets .nav--more on the list while it is not scrolled to its
   end, on the desktop and in the phone drawer alike; the fade rides the
   bottom of whichever box scrolls (sticky), lets clicks through, and leaves
   with a 160ms fade once the last row is in view. */
.nav::after{content:"";position:sticky;bottom:0;display:block;height:40px;margin-top:-40px;
  pointer-events:none;background:linear-gradient(to bottom,transparent,var(--nav) 88%);
  opacity:0;transition:opacity var(--t-fast) var(--ease-state)}
.nav--more::after{opacity:1}

/* dark mode only: at 1.39:1 the column stops reading as a column without an edge.
   Light mode is 12.89:1 and must not get a border. */
:root:not([data-theme="light"]){ @media (prefers-color-scheme: dark){
  .side{border-right:1px solid var(--line)}
}}
:root[data-theme="dark"] .side{border-right:1px solid var(--line)}

/* ==========================================================================
   THE FOLD
   Above 1000px the reader can put the column away and read the page alone.
   At 1000px and below the column is the phone drawer and none of this
   applies. The reader hides it; nothing hides it by default (HIG, sidebars).
   The query is (width > 1000px), the exact complement of the drawer's
   (max-width:1000px). min-width:1001px would leave a zoomed window between
   1000 and 1001px with the column open and no button to fold it.

   build.py's shell() writes two buttons and a script in <head>. The script
   sets <html data-side="open">, or "closed" if the reader closed the column
   on an earlier page, before anything paints, so no page opens with the
   column and then slides it away. Without JavaScript there is no data-side:
   both buttons stay hidden and the column stays open. The choice lives in
   localStorage, read and written in try/catch; where storage is refused the
   column opens as on a first visit.

   The hide button sits on the column, top right beside his portrait, and
   leaves with it. The show button waits on the page at the top left, one
   layer under the column: the column uncovers it as it slides away and
   covers it again as it returns. Both sit at --fold-top, centred on the
   portrait (y=56, or 45 in a short window), so the eye finds the way back
   where it found the way out. The folded page keeps a 56px margin for that
   button (8px, the 40px button, 8px), so nothing ever scrolls under it. A
   document page pads its text by 32px, and without the margin its crumb and
   contents list would run under the button at any width below 1300px.

   The button shares the portrait's row, so the name under it has the whole
   column width (164px of 200). That holds only while the identity has the
   whole width: a classic 15px scrollbar would take it from under the name
   in a short window. So on the desktop the identity stays put and only the
   list scrolls, under a thin scrollbar in the column's own blue (the thumb
   is 3.19:1 on --nav). The portrait, the name and the button never move.

   The returning column covers the spot where the show button was, and that
   spot is the name, the link home. The second click of a double-click
   would land there and leave the page, so shell()'s script drops a pointer
   press that lands off the buttons within 500ms of a fold, the Windows
   double-click time. Keyboard clicks are never dropped.

   Motion: the column slides its own width while .main's margin follows,
   both 240ms on --ease, the phone drawer's own pair. From 1260px .wrap keeps
   its 1020px in both states, so the text does not rewrap; the column only
   moves. These are transitions, so a second click midway turns the motion
   round from where it is. Under reduced motion build.py's floor drops every
   transition and the column is simply gone, or back.
   ========================================================================== */
.fold{display:none;position:absolute;top:var(--fold-top);right:8px;z-index:1;place-items:center;
  width:40px;height:40px;margin:0;padding:0;border:0;border-radius:var(--r-sm);
  background:transparent;color:var(--muted);font:inherit;cursor:pointer;
  -webkit-tap-highlight-color:transparent;
  transition-property:background-color,color,transform,visibility;
  transition-duration:var(--t-quick),var(--t-quick),var(--t-quick),0s;
  transition-timing-function:var(--ease-state),var(--ease-state),var(--ease),linear}
.fold::before{content:"";position:absolute;inset:-2px}    /* a 44px target */
.fold svg{display:block;pointer-events:none}
.fold--show{position:fixed;left:8px;right:auto;z-index:39}  /* under .side's 40 */
@media (hover:hover){
  .fold:hover{background:color-mix(in oklab,var(--ink) 5%,var(--page));color:var(--ink)}
}
/* pressed: one step deeper, as a row is, and the button gives a little under
   the finger, as the hero's two controls do */
.fold:active{background:color-mix(in oklab,var(--ink) 8%,var(--page));transform:scale(.97)}
.fold:focus-visible{outline:2px solid var(--focus);outline-offset:2px;color:var(--ink)}
/* the glyph previews the click: the pane's edge moves 3 units the way the
   column is about to go, and back when the pointer leaves. A key that lands
   on the button finds the edge there already: keyboard focus takes the end
   state at once, the travel is the pointer's */
@media (prefers-reduced-motion:no-preference){
  .fold__edge{transition:transform var(--spring-fast)}
  .fold--hide:focus-visible .fold__edge{transform:translateX(-3px);transition:none}
  .fold--show:focus-visible .fold__edge{transform:translateX(3px);transition:none}
}
@media (hover:hover) and (prefers-reduced-motion:no-preference){
  .fold--hide:hover .fold__edge{transform:translateX(-3px)}
  .fold--show:hover .fold__edge{transform:translateX(3px)}
}
@media (forced-colors:active){.fold{border:1px solid ButtonBorder}}

@media (width > 1000px){
  [data-side] .fold{display:grid}
  /* the identity row holds the button, so only the list scrolls; the navy
     under the last row gives way to the list before the list scrolls */
  [data-side] .side{overflow:hidden}
  [data-side] .side__end{min-height:0}
  [data-side] .nav{flex:1 1 auto;min-height:0;overflow-y:auto;
    overscroll-behavior:contain;scrollbar-width:thin;
    scrollbar-color:color-mix(in oklab,var(--nav-ink) 40%,var(--nav)) transparent}
  .side{transition:transform var(--spring-mid),visibility 0s}
  .main{transition:margin-left var(--t-mid) var(--ease)}
  /* hidden once it has slid away, so it leaves the tab order too */
  [data-side="closed"] .side{transform:translateX(-100%);visibility:hidden;
    transition:transform var(--spring-mid),visibility 0s linear var(--t-mid)}
  [data-side="closed"] .main{margin-left:56px}   /* the show button's margin */
  /* the show button exists only while the column is away: it turns visible
     at once, and hidden only after the returning column has covered it */
  .fold--show{visibility:hidden;transition-delay:0s,0s,0s,var(--t-mid)}
  [data-side="closed"] .fold--show{visibility:visible;transition-delay:0s}
  /* a page restored from the back-forward cache takes the reader's latest
     choice without replaying the slide */
  .side-still :is(.side,.main,.fold){transition:none!important}
}

/* ==========================================================================
   THE MASTHEAD
   The home page opens with his sentence on waves and data in a band across
   the top, as his slides 1 and 4 draw it. parts/masthead.py draws the band;
   build.py's shell() sets it first in <main>, in <div class="mastrow">.
   It spans the page from the column's edge to the window's, level with the
   name: the name and the band make the top of the page, and the column runs
   down from under the name. It does not cross the column. A band over the
   column would either cover the name or push the column, its name and its
   rows down on this one page, so the site's navigation would jump
   between the home page and the rest; here nothing in the column moves.
   Since 26 Sep 2026 it is a slim band, shorter than the name block beside
   it (the client asked for it thinner, so the illustration under it is
   seen as the page opens). Folded, the band follows .main to the show button's margin, and
   on a phone it is the first thing under the top bar.
   ========================================================================== */
.mastrow{position:relative}

@media (prefers-reduced-motion:reduce){
  .nav a::before,.nav a::after,.id::before{transition:none}
}

/* ==========================================================================
   PRINT: the text without the column or the phone bar
   ========================================================================== */
@media print{
  .side,.bar,.fold{display:none!important}
  .main{margin-left:0!important}
}

"""

CSS = CSS.replace("  /*SPRINGS*/\n", "".join(
    f"  --spring-{name}:{settle}ms {easing};\n" for name, (_, settle, easing) in SPRINGS.items()))

JS = r"""
/* A calm entrance as sections scroll into view: the page's h2s, cards and
   rows rise 12px and fade in. The class goes on only when motion is welcome
   and IntersectionObserver exists, so without it everything simply shows. */
if(!('IntersectionObserver' in window)||matchMedia('(prefers-reduced-motion: reduce)').matches)return;
var sel='.main .wrap > h2,.abt__glance > *,.cv section,.find li,.typed figure,.gal figure,.blog__list > li';
var els=[].slice.call(document.querySelectorAll(sel)).filter(function(e){return e.getBoundingClientRect().top>innerHeight*.9});
if(!els.length)return;
els.forEach(function(e){e.classList.add('rv')});
var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){
  var e=x.target,sib=[].slice.call(e.parentNode.children).filter(function(c){return c.classList.contains('rv')&&!c.classList.contains('in')});
  e.style.transitionDelay=Math.min(sib.indexOf(e),4)*70+'ms';e.classList.add('in');io.unobserve(e)}})},{rootMargin:'0px 0px -8% 0px'});
els.forEach(function(e){io.observe(e)});
"""


def render(**_kw):
    """The theme carries no markup."""
    return ""
