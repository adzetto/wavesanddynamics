# -*- coding: utf-8 -*-
"""docs - the document pages, doc/<slug>.html.

Renders no markup: build.py's page_doc() writes it from preview.py and puts
`docpage` on the page's .wrap, so every selector here sits under .docpage.

ONE COLUMN. Text, pictures, tables, callouts, captions and the title share
one width, --measure-doc (672px): 75.6 characters a line at 19px, and the
ML guide's own column in Word. The client asked for exactly this: his
figures and tables used to break out to the right, up to 924px, past a
608px measure, so a page had three right edges. The column is centred in
the space the site's column leaves, and folding that column away moves the
text but never rewraps it. A picture he set narrower in Word keeps that
share of the column, never under 60% of it and never past its own pixels
(build.py, preview.py); a table that cannot fit scrolls inside the column,
and says so with a shadow at the edge that has more.

THE CONTENTS. A document four sections long or more has a contents list in
the text, where his own "Table of Contents" line stood: a <details open>
that folds, and with no script the only one. The client asked for it to
stand out, so it is a card: the one block of a page that is only a way
round it, set apart by the site's card fill (no border, no shadow). Its
first row is the toggle and says what it will do: the list's mark, his
label in ink, and "Hide" or "Show" beside a chevron that points the way
the list will go. Shut, the card is that row alone with its count of
sections; the list leaves no space behind. The rows are numbered, 48px at
least: his own numbers where his headings carry them (the ML guide), the
list's count where they do not, in a gutter the titles hang clear of.

With the script there is also a dock: one button, "Contents", the card
made small, pinned beside the top of the column as the reader scrolls,
and the list it opens, numbered the same way. The rule that decides where
the list opens is the margin: at 1424px and up with the site's column open,
and 1240px and up with it folded, the space left of the column holds a
200px list with 32px to spare, so the list opens there, in the margin,
and the text never moves. From 1280px with the column open and 1100px with
it folded the margin still holds it, set smaller (13.5px, 148 to 211px
wide, two lines a title but the one being read): the professor asked for the sections to be followed from the side
on a laptop too (5 Oct 2026). Narrower, a list in the margin would have to
push the text or sit on it, so it opens over the text instead, from the left
edge of the page, with a soft scrim; Escape, a click outside and choosing a
section all close it, and choosing a section jumps to it. On a phone or a
tablet (1000px and less) there is no margin at all: the list stays in the
text, and a small Contents pill floats in while the list is out of sight:
from the top of a document whose list sits far down (the ML guide opens with
a long preface, and its list is four screens down on a phone), and again
once the reader has passed the list and scrolls back up, opening the list as
a sheet from the foot of the screen. Beside the column (1001px up) the
button likewise shows only while the card in the text is off screen, so the
page never offers two Contents at once; where the list lies in the margin
the button is its toggle and always shows.

Closed is nothing: the list goes, the button stays. Open, the list marks
the section being read with one warm mark and opens scrolled to it. The
card in the text keeps the last chapter read marked the way the site's
column marks its page, a 3px warm rail and the title in ink, so a reader
who comes back up to it finds where they were; colour and a mark only,
nothing in the row moves. Where the list lies in the margin it starts
open, since it covers nothing, and the reader's choice to shut it is kept
from page to page (localStorage, read in <head> before the first paint,
so no page opens with the list only to shut it). Where it would lie over
the text it always starts shut: a list that covers the text is only ever
asked for. The list comes in 240ms on the
site's --ease and goes in 160ms, the way it came: out of the margin's top,
in from the page's left edge, up from the foot of the screen; the moves are
CSS transitions, so a second click turns one round midway, and reduced
motion drops them. The card's list opens and shuts at once, so the long
text under it is laid out once, never on every frame; opening, its rows
fade in and settle 4px into place, and its chevron turns. Focus goes into
the list when it opens and back to the button when it closes.

Tables know how they fold: most restack on a phone one row to a block, each
value under its column's name; a matrix and a wide grid of short values
scroll sideways with their row names held.
"""

__all__ = ["CSS", "JS", "render"]

# The contents in the margin: the same rules at two widths, one for each
# state of the site's column. %P% is the attribute that says which.
_MARGIN = """
  %P%[data-toc] .docpage.has-toc>.tocdock{width:min(280px,calc(100% - 32px));margin:-10px 32px 0 0}
  %P%[data-toc] .docpage.has-toc .toc--body,
  %P%[data-toc] .docpage.has-toc>.tocscrim{display:none}
  %P% .docpage .tocbtn__t{position:static;clip-path:none;width:auto;height:auto;overflow:visible;
    white-space:nowrap}
  %P% .docpage .tocbtn{min-height:44px;padding:0 16px 0 12px}
  %P% .docpage .tocpanel{position:relative;inset:auto;z-index:auto;width:auto;
    max-height:calc(100vh - 96px);
    margin-top:12px;padding:0 0 24px;background:none;box-shadow:none;transform:none;
    visibility:visible;opacity:1;
    transition:opacity var(--t-mid) var(--ease),transform var(--spring-mid)}
  %P%[data-toc="closed"] .docpage .tocpanel{visibility:hidden;opacity:0;transform:translateY(-6px);
    transition:opacity var(--t-fast) var(--ease-state),transform var(--t-fast) var(--ease-state),
      visibility 0s linear var(--t-fast)}
  %P% .docpage .tocpanel__head{display:none}
  %P% .docpage .tocpanel{--tm:0px}
  %P% .docpage .toc--rail{--tl:10px;--tg:30px}
  %P% .docpage .toc--rail a{color:var(--muted);font-size:15px}
  %P% .docpage .toc--rail ol ol a{font-size:14px}
"""

# The contents in a narrower margin (the professor, 5 Oct 2026: "a bar on the
# side that follows the sections", on a laptop where the margin had only the
# button): the same list, laid in the margin the same way (_MARGIN), in a
# smaller size that fits 148 to 211px, from 1280px with the site's column
# open and from 1100px with it folded. A title takes three lines at most, but
# the one being read, which shows whole (two cut both case studies of the
# waves guide to "Case Study: Wave..."); the rows' air is a clear border, so
# the lines cut off stay out of it.
_COMPACT = """
  %P%[data-toc] .docpage.has-toc>.tocdock{width:calc(100% - 20px);margin:-10px 12px 0 0}
  %P% .docpage .toc--rail{--tl:6px;--tg:22px}
  %P% .docpage .toc--rail a{padding:0 4px 0 calc(var(--tl) + var(--tg));
    border-block:5px solid transparent;font-size:13.5px;line-height:1.3;
    display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;overflow:hidden}
  %P% .docpage .toc--rail a[aria-current]{-webkit-line-clamp:none}
  %P% .docpage .toc--rail ol ol a{border-block-width:4px;font-size:12.5px}
  %P% .docpage .toc__list>li>a>.hn:first-child,
  %P% .docpage .toc__list>li>a:not(:has(>.hn))::before{top:0}
"""

# A restacked table, on a phone and wherever a table cannot fit: one row to a
# block under the row's name, the rule in ink over the first; each value under
# its column's name, or beside it where every value is a phrase (tbl--kv): a
# column of names the eye runs down, the values on one edge. %T% is the
# selector of the tables it restacks.
_STACK = """
  .docpage %T% :is(table,thead,tbody,tr,th,td){display:block;width:auto}
  .docpage %T% thead{position:absolute;width:1px;height:1px;overflow:hidden;
    clip-path:inset(50%);white-space:nowrap}
  .docpage %T% colgroup{display:none}
  .docpage %T% tr{padding:16px 0;border-bottom:1px solid var(--rule)}
  .docpage %T% tbody tr:last-child{border-bottom:0}
  .docpage %T% tr>*,.docpage %T% tr>.c,
  .docpage %T% tr>.c:not(:last-child){padding:0;border:0;text-align:left}
  .docpage %T% tr>*+*{margin-top:10px}
  .docpage %T% td:empty{display:none}
  .docpage %T% th[scope=row]{font-size:17px;line-height:1.35;font-weight:600}
  .docpage %T% td{font-size:15px}
  .docpage %T% td[data-label]::before{content:attr(data-label);
    content:attr(data-label) / "";display:block;
    margin:0 0 3px;font:600 11px/1.35 var(--sans);letter-spacing:.09em;
    text-transform:uppercase;color:var(--muted)}
  .docpage %T%.tbl--kv td[data-label]{display:grid;grid-template-columns:minmax(0,34%) minmax(0,1fr);
    column-gap:16px}
  .docpage %T%.tbl--kv td[data-label]::before{grid-row:1 / span 9;margin:6px 0 0}  /* on the value's baseline */
  .docpage %T%.tbl--kv td[data-label]>*{grid-column:2}
  .docpage %T%.tbl--kv tr>td+td{margin-top:8px}
  /* a row's note stays under its values, at the column's width */
  .docpage %T%.tbl--notes.tbl--kv tr>td:last-child{display:block;margin-top:12px}
  .docpage %T%.tbl--notes td:last-child::before{margin:0 0 3px}
  .docpage %T%.tbl--notes td:last-child{font-size:14px;line-height:1.45;color:var(--muted)}
  /* more of a group: the name it repeats steps down to the text's size */
  .docpage %T% tr:has(+.tr-same){border-bottom-color:transparent}
  .docpage %T% .tr-same{padding-top:4px}
  .docpage %T% .tr-same>th[scope=row]{font-size:15px;font-weight:400}
  .docpage %T% .c figure img{margin-inline:0}
  /* a picture and his words about it (the waves guide's fun table): the
     picture beside the row's name, as wide as the column gives it on a wide
     screen, its label under it; his words under both, the column's width */
  .docpage %T%.tbl--fig tr{display:grid;grid-template-columns:minmax(0,50%) minmax(0,1fr);
    column-gap:16px;align-items:start}
  .docpage %T%.tbl--fig tr>*{grid-column:1 / -1}
  .docpage %T%.tbl--fig tr>.c.pic{grid-column:1;grid-row:1;text-align:center}
  .docpage %T%.tbl--fig tr>th[scope=row]{grid-column:2;grid-row:1;align-self:center}
  .docpage %T%.tbl--fig tr>*+*{margin-top:0}
  .docpage %T%.tbl--fig tr>:not(.pic,th){margin-top:14px}
  .docpage %T%.tbl--fig .c figure img{margin-inline:auto}
"""

CSS = """
/* His formulas, set by mathtex.py from each document's map, in Latin Modern
   Math cut down as Site Math: the face LaTeX sets them in. Where the text
   around is bold (a heading, a bold cell, <strong>) the bold face takes over,
   Latin Modern's own bold math letters and figures, as LaTeX's boldmath:
   never a synthesized weight. Inline, at the size that gives its x-height the
   text's (Source Serif 4 .475em, Latin Modern .431em: 1.1em). .docpage
   math.im outranks blog.py's older .typed math. The ink is the text's. */
@font-face{font-family:"Site Math";src:url(fonts/site-math.woff2) format("woff2");
  font-display:block}
@font-face{font-family:"Site Math";font-weight:600 900;
  src:url(fonts/site-math-bold.woff2) format("woff2");font-display:block}
math{font-family:"Site Math",math}
.docpage math.im{font-family:"Site Math",math;font-size:1.1em;font-weight:inherit;
  font-synthesis:none}
/* A formula and the characters touching it never part at a line's end (.im-nb
   runs from space to space). A long formula is set in pieces that may part
   where TeX breaks one, after a relation or a binary operator; what is read
   is the whole formula, kept out of sight (.im-sr). */
.docpage .im-nb{white-space:nowrap}
.docpage .im-sr{position:absolute;width:1px;height:1px;overflow:hidden;
  clip-path:inset(50%);white-space:nowrap}
/* A display formula stands centred on its own line. Where the column is
   narrower than it, a long one's pieces take lines of their own, and a line
   still too wide is set smaller to fit, down to .66em (--mw: its widest line
   in em, from mathtex.py; the container is its paragraph); past that it
   scrolls sideways. The padding keeps its tallest glyphs clear of the
   scroller's edge. */
.docpage :is(p,li,.eq):has(>math.im[display=block],>.im-dm){container-type:inline-size}
.docpage math.im[display=block],.docpage .im-dm{
  font-size:max(.66em,min(1.1em,100cqi / var(--mw,.01)));
  margin:.3em 0;padding:.25em 0;overflow-x:auto;overflow-y:hidden}
.docpage .im-dm{display:block;text-align:center}
.docpage .im-dm>math.im{font-size:1em}
.docpage .eq>:is(math.im[display=block],.im-dm){flex:1;min-width:0;
  font-size:max(.66em,min(1.1em,(100cqi - 3.5em) / var(--mw,.01)))}
/* ===================== the document pages ===================== */
/* one column, centred in what the site's column leaves; 16px of padding
   beside it on a wide screen gives the margins every pixel for the contents */
.docpage{--side-now:var(--side);max-width:none;display:grid;
  grid-template-columns:minmax(0,1fr) minmax(0,var(--measure-doc)) minmax(0,1fr);
  padding-inline:16px}
[data-side="closed"] .docpage{--side-now:56px}
.docpage>*{grid-column:2;min-width:0}
.docpage>.crumb{grid-row:1}
.docpage>.docart{grid-row:2}
.foot.foot--doc{max-width:calc(var(--measure-doc) + 96px)}

/* ---------- where the page lives: back to My Research Areas, the Big Picture
   or the Blog. His three guides are rows of the column and have none. ---------- */
.docpage .crumb{margin:-10px 0 20px}
.docpage .crumb a{display:inline-flex;align-items:center;gap:4px;min-height:44px;
  margin-left:-6px;padding:0 10px 0 2px;border-radius:var(--r-sm);
  font:600 14px/1.2 var(--sans);letter-spacing:.01em;color:var(--muted);text-decoration:none;
  transition:color var(--t-fast) var(--ease-state)}
.docpage .crumb svg{flex:none}

/* ---------- his cover is the header ---------- */
.docpage .dochead{margin:0 0 40px;padding:0 0 32px;border-bottom:1px solid var(--rule)}
.docpage .dochead figure{margin:0 0 36px;max-width:none}
.docpage .dochead figure img{display:block;max-width:100%;height:auto;border-radius:var(--r-md)}
.docpage .dochead__pre{margin:0 0 12px;font-size:16px;line-height:1.5;color:var(--muted)}
.docpage .dochead__rule{margin:0 0 28px;border:0;border-top:1px solid var(--line)}
.docpage .dochead h1{margin:0;text-wrap:balance}
.docpage .dochead__dek{margin:16px 0 0;font-size:21px;line-height:1.45;
  letter-spacing:-.004em;color:var(--body);text-wrap:pretty}
.docpage .dochead__by{margin:14px 0 0;font-size:16px;line-height:1.5;color:var(--muted)}

/* the Word download reads as it does under the research boxes: the mark, a
   body link, the size in --muted */
.docpage .docmeta{margin:12px 0 0}
.docpage .docdl{display:inline-flex;align-items:center;gap:8px;min-height:44px;
  color:var(--link);text-decoration:none;border-radius:var(--r-sm);
  font:600 14px/1.3 var(--sans);letter-spacing:.01em}
.docpage .docdl svg{flex:none;width:20px;height:20px;margin-left:-5px}
.docpage .docdl__t{text-decoration-line:underline;text-decoration-thickness:1.5px;
  text-underline-offset:3px;
  text-decoration-color:color-mix(in oklab,currentColor,transparent 62%);
  transition:text-decoration-color var(--t-fast) var(--ease-state)}
.docpage .docdl__size{color:var(--muted);font-variant-numeric:lining-nums tabular-nums}

/* ---------- the contents ---------- */
/* One glyph means "contents" wherever the list opens: the list mark on the
   dock's button, drawn again as a mask so the card in the text and the
   panel's head wear it too, without markup of their own */
.docpage{--toc-ico:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='1.5' stroke-linecap='round'%3E%3Cpath d='M9 6.5h11M9 12h11M9 17.5h11M4.5 6.5h.01M4.5 12h.01M4.5 17.5h.01'/%3E%3C/svg%3E")}
.docpage nav.toc ol{list-style:none;margin:0;padding:0}
.docpage nav.toc li{margin:0}              /* not the text's .45em: the rows touch */
.docpage .toc a{--num:var(--muted);position:relative;display:block;color:var(--body);text-decoration:none;
  text-wrap:balance;font-variant-numeric:lining-nums proportional-nums;
  transition:background-color var(--t-quick) var(--ease-state),color var(--t-quick) var(--ease-state)}
/* Numbered. His own numbers where his headings carry them (.hn, the ML
   guide), else the list's count. Either stands in a gutter at the row's
   left, right-aligned, in the title's own face and size so the two share a
   baseline, and a title that wraps hangs clear of it. The count only draws
   the <ol>'s order, so screen readers, which already say "1 of 10", skip it */
.docpage .toc--body ol,.docpage .toc__list{counter-reset:toc}
.docpage .toc--body li,.docpage .toc__list>li{counter-increment:toc}
.docpage :is(.toc--body li,.toc__list>li)>a{padding-left:calc(var(--tl) + var(--tg))}
.docpage :is(.toc--body li,.toc__list>li)>a>.hn:first-child,
.docpage :is(.toc--body li,.toc__list>li)>a:not(:has(>.hn))::before{position:absolute;
  left:var(--tl);width:calc(var(--tg) - .6em);text-align:right;white-space:nowrap;
  color:var(--num);font-variant-numeric:lining-nums tabular-nums}
.docpage :is(.toc--body li,.toc__list>li)>a:not(:has(>.hn))::before{
  content:counter(toc) ".";content:counter(toc) "." / ""}

/* ---------- the contents in the text: a card ---------- */
/* The one block of a document that is only a way round it, so it is set
   apart: a card of --card, the site's card fill (body 7.07:1 and muted
   4.67:1 on it), no border, no shadow. Its first row is the toggle and says
   so: the mark, his label in ink, and at the right "Hide" or "Show" beside a
   chevron that points the way the list will go. Shut, the card is that row
   alone, with the count of its sections; the list leaves no space behind.
   The transparent border is the card's edge where forced colours paint no
   fill */
.docpage .toc--body{--tl:18px;--tg:36px;max-width:none;margin:0 0 48px;
  border:1px solid transparent;border-radius:var(--r-md);background:var(--card);
  overflow:hidden;overflow:clip}
.docpage .doc .toc--body{margin:40px 0 48px}
.docpage .toc__sum{display:flex;align-items:center;column-gap:10px;list-style:none;
  cursor:pointer;-webkit-tap-highlight-color:transparent;-webkit-user-select:none;
  user-select:none;transition:background-color var(--t-quick) var(--ease-state)}
.docpage .toc__sum::-webkit-details-marker{display:none}
/* the mark stands in the numbers' gutter and his label on the titles' edge */
.docpage .toc--body .toc__sum{min-height:60px;padding:8px 12px 8px calc(var(--tl) + var(--tg) - 30px);
  color:var(--ink)}
.docpage :is(.toc--body .toc__sum,.tocpanel__head)::before{content:"";flex:none;
  width:20px;height:20px;background:currentColor;
  -webkit-mask:var(--toc-ico) center/20px 20px no-repeat;mask:var(--toc-ico) center/20px 20px no-repeat}
.docpage .toc__h{font:600 17px/1.25 var(--sans);letter-spacing:.005em;color:var(--ink)}
.docpage .toc__n{order:1;font:400 14px/1.2 var(--sans);letter-spacing:.01em;color:var(--muted);
  font-variant-numeric:lining-nums;white-space:nowrap;opacity:0}
.docpage .toc__n::before{content:"\\B7";padding-right:8px}
.docpage .toc__fold:not([open]) .toc__n{opacity:1}
/* the words are drawn, and hidden from screen readers, which hear the
   summary's own "expanded" or "collapsed" */
.docpage .toc--body .toc__sum::after{order:2;margin-left:auto;padding-left:12px;
  content:"Hide";content:"Hide" / "";font:600 14px/1.2 var(--sans);letter-spacing:.01em;
  color:var(--muted);transition:color var(--t-quick) var(--ease-state)}
.docpage .toc--body .toc__fold:not([open]) .toc__sum::after{content:"Show";content:"Show" / ""}
.docpage .toc__chev{order:3;flex:none;margin-left:-6px;color:var(--muted);transform:rotate(-90deg);
  transition:color var(--t-quick) var(--ease-state)}
.docpage .toc__fold:not([open]) .toc__chev{transform:rotate(90deg)}

/* a row per chapter, 48px at least, the fill running to the card's edges;
   the hairlines start where the titles do */
.docpage .toc--body li{position:relative}
.docpage .toc--body li:last-child{padding-bottom:8px}
.docpage .toc--body li+li::before{content:"";position:absolute;top:0;right:0;
  left:calc(var(--tl) + var(--tg));border-top:1px solid var(--rule)}
.docpage .toc--body li>a{min-height:48px;padding-top:12px;padding-right:20px;padding-bottom:12px;
  font-size:17px;line-height:1.4}
.docpage .toc--body li>a>.hn:first-child,
.docpage .toc--body li>a:not(:has(>.hn))::before{top:12px}
/* coming back up to the list, the reader finds the section they were in
   marked as the site's column marks its page: a 3px warm rail at the row's
   edge, and the title in ink. Colour and a mark only; nothing in the row
   moves or rewraps */
.docpage .toc--body li>a::after{content:"";position:absolute;left:0;top:10px;bottom:10px;width:3px;
  border-radius:0 var(--r-pill) var(--r-pill) 0;background:var(--accent);opacity:0;
  pointer-events:none}
.docpage .toc--body li>a.is-last{color:var(--ink)}
.docpage .toc--body li>a.is-last::after{opacity:1}
/* a phone has no room for the count beside his label and the toggle's word */
@media (max-width:480px){
  .docpage .toc--body .toc__n{display:none}
}

/* the fold: the list takes its height, or gives it up, at once, so the long
   document under it is laid out once, not on every frame (an eased height
   laid out 74,000px of the ML guide each frame). The chevron turns; opening,
   the rows fade in and settle 4px into place (the script's, on the reader's
   own click only, so nothing moves as the page loads); shutting, they go at
   once. Reduced motion keeps the end states */
@media (prefers-reduced-motion:no-preference){
  .docpage .toc__chev{transition:transform var(--spring-mid),
    color var(--t-quick) var(--ease-state)}
  .docpage .toc__n,.docpage .toc--body li>a::after,.docpage .toc--body li+li::before{
    transition:opacity var(--t-fast) var(--ease-state)}
}

/* ---------- the dock: the Contents button, and the list it opens ---------- */
/* without the script neither exists: the list in the text is the contents */
.docpage .tocdock,.docpage .tocscrim{display:none}
/* the button is the card made small: the same fill, the same mark, and
   "Contents" in ink */
.docpage .tocbtn{position:relative;display:inline-flex;align-items:center;gap:8px;
  min-width:44px;min-height:44px;margin:0;padding:0 16px 0 12px;border:1px solid transparent;
  border-radius:var(--r-pill);background:var(--card);color:var(--ink);cursor:pointer;
  font:600 15px/1.2 var(--sans);letter-spacing:.01em;-webkit-tap-highlight-color:transparent;
  transition:background-color var(--t-quick) var(--ease-state),transform var(--spring-fast)}
.docpage .tocbtn svg{flex:none}
/* the label is the button's name everywhere; where the margin is too narrow
   to show it, it shows on hover and on focus, below the button */
.docpage .tocbtn__t{position:absolute;width:1px;height:1px;overflow:hidden;
  clip-path:inset(50%);white-space:nowrap}
.docpage .tocpanel{position:relative;overflow-y:auto;overscroll-behavior:contain;
  scrollbar-width:thin;scrollbar-color:var(--line) transparent}
/* the head's mark stands in the numbers' gutter and his label on the titles'
   edge, as in the card (--tm is how far the track sits in) */
.docpage .tocpanel__head{display:flex;align-items:center;gap:10px;min-height:60px;
  padding:4px 4px 4px calc(var(--tm) + 1px + var(--tl) + var(--tg) - 30px);
  position:sticky;top:0;z-index:1;background:var(--page);color:var(--ink)}
.docpage .tocpanel__x{flex:none;display:grid;place-items:center;width:44px;height:44px;
  margin:0 0 0 auto;padding:0;border:0;border-radius:var(--r-sm);background:transparent;
  color:var(--muted);cursor:pointer;-webkit-tap-highlight-color:transparent;
  transition:background-color var(--t-quick) var(--ease-state),color var(--t-quick) var(--ease-state)}
.docpage .tocpanel__x svg{display:block}

/* the list in the dock: a hairline track, and one warm mark on it for "you
   are here". Only the chapter being read shows its sections where a pointer
   picks: 38px rows (WCAG 2.5.8 asks 24) keep the guide's twelve chapters and
   the open one's sections in an 800px screen. A touch screen gets 46px rows,
   every chapter open: a list that opens under a finger moves the rows below
   it */
.docpage .toc--rail{--tl:14px;--tg:33px;--tm:16px}
.docpage .toc__track{position:relative;margin-left:var(--tm)}
.docpage .toc__list{border-left:1px solid var(--rule)}
.docpage .toc--rail a{padding:8px 10px 8px var(--tl);font-size:16px;line-height:1.35;
  border-radius:0 var(--r-sm) var(--r-sm) 0}
.docpage .toc__list>li>a>.hn:first-child,
.docpage .toc__list>li>a:not(:has(>.hn))::before{top:8px}
.docpage .toc--rail li>ol{display:none;margin:0 0 6px}
.docpage .toc--rail li.is-open>ol{display:block}
.docpage .toc--rail ol ol a{padding-block:6px;padding-left:calc(var(--tl) + var(--tg));font-size:15px}
.docpage .toc--rail ol ol .hn{margin-right:.3em}
@media (pointer:coarse){
  .docpage .toc--rail a{padding-block:12px}
  .docpage .toc__list>li>a>.hn:first-child,
  .docpage .toc__list>li>a:not(:has(>.hn))::before{top:12px}
  .docpage .toc--rail ol ol a{padding-block:10px}
  .docpage .toc--rail li>ol{display:block}
}
.docpage .toc--rail a[aria-current],.docpage .toc--rail li.is-open>a{color:var(--ink)}
.docpage .toc__mark{position:absolute;top:0;left:-1px;width:3px;height:1px;
  background:var(--accent);transform-origin:0 0;opacity:0;pointer-events:none}
.docpage .toc__mark.is-on{opacity:1}
@media (forced-colors:active){
  .docpage :is(.toc--body .toc__sum,.tocpanel__head)::before{forced-color-adjust:none;
    background:CanvasText}
  .docpage .toc__mark{width:0;background:none;border-left:3px solid Highlight}
  .docpage .toc--body li>a::after{width:0;background:none;border-left:3px solid Highlight}
  .docpage .tocpanel{border:1px solid CanvasText}
}
@media (prefers-reduced-motion:no-preference){
  .docpage .tocpanel{scroll-behavior:smooth}
  .docpage .toc__mark{transition:transform var(--spring-mid),
    opacity var(--t-fast) var(--ease-state)}
  .docpage .tocbtn:active{transform:scale(.97)}
}

/* over the text: the margin cannot hold the list. The button waits beside
   the column; the list comes in from the page's left edge, from under the
   site's column, over a soft scrim, and goes back the way it came */
@media (width > 1000px){
  /* the dock sits over the scrim, the list in it under the site's column.
     Where the margin is too narrow for the word (1024px with the column open
     leaves 48px) the button is its mark, drawn at 36px and touched at 44,
     centred between the site's column and the text */
  [data-toc] .docpage.has-toc>.tocdock{display:block;grid-column:1;grid-row:1 / span 2;
    justify-self:end;align-self:start;position:sticky;top:16px;z-index:39;
    margin:-6px 6px 0 0}                          /* centred on the crumb's row */
  .docpage .tocbtn{min-width:36px;min-height:36px;padding:0 7px}
  .docpage .tocbtn::after{content:"";position:absolute;inset:-4px}
  [data-toc] .docpage.has-toc>.tocscrim{display:block;position:fixed;
    inset:0 0 0 var(--side-now);z-index:38;background:rgba(39,34,28,.16);
    opacity:0;visibility:hidden;
    transition:opacity var(--t-fast) var(--ease-in-out),visibility 0s linear var(--t-fast)}
  [data-tocpanel] .docpage.has-toc>.tocscrim{opacity:1;visibility:visible;
    transition:opacity var(--t-mid) var(--ease)}
  .docpage .tocpanel{position:fixed;top:0;bottom:0;left:var(--side-now);
    width:min(360px,calc(100vw - var(--side-now) - 64px));padding:0 12px 24px 0;
    background:var(--page);box-shadow:var(--sh-3);
    transform:translateX(-100%);visibility:hidden;
    transition:transform var(--t-fast) var(--ease-in-out),visibility 0s linear var(--t-fast)}
  [data-tocpanel] .docpage .tocpanel{transform:none;visibility:visible;
    transition:transform var(--spring-mid)}
  /* the button fades in once the card in the text is off screen (the
     script's .is-on): one Contents on screen at a time. The margin layouts
     below keep it, as the list's toggle */
  .docpage .tocbtn{transition:opacity var(--t-fast) var(--ease-state),
    visibility 0s linear var(--t-fast),background-color var(--t-quick) var(--ease-state),
    transform var(--spring-fast)}
  .docpage .tocbtn.is-on,[data-tocpanel] .docpage .tocbtn{
    transition:opacity var(--t-mid) var(--ease),visibility 0s,
      background-color var(--t-quick) var(--ease-state),transform var(--spring-fast)}
  /* the label under a button that is only its mark */
  .docpage .tocbtn:is(:hover,:focus-visible) .tocbtn__t{top:calc(100% + 6px);left:0;width:auto;
    height:auto;padding:6px 10px;clip-path:none;border-radius:var(--r-sm);
    background:var(--ink);color:var(--page);font:600 12px/1.2 var(--sans);letter-spacing:.06em;
    box-shadow:var(--sh-2);pointer-events:none}
}
/* with room for its word the button says it */
@media (min-width:1188px){
  [data-toc] .docpage.has-toc>.tocdock{margin:-10px 12px 0 0}
  .docpage .tocbtn{min-height:44px;padding:0 16px 0 12px}
  .docpage .tocbtn__t,.docpage .tocbtn:is(:hover,:focus-visible) .tocbtn__t{position:static;
    width:auto;height:auto;padding:0;clip-path:none;background:none;color:inherit;
    box-shadow:none;font:inherit;letter-spacing:inherit}
}
@media (min-width:1004px){
  [data-side="closed"][data-toc] .docpage.has-toc>.tocdock{margin:-10px 12px 0 0}
  [data-side="closed"] .docpage .tocbtn{min-height:44px;padding:0 16px 0 12px}
  [data-side="closed"] .docpage .tocbtn__t,
  [data-side="closed"] .docpage .tocbtn:is(:hover,:focus-visible) .tocbtn__t{position:static;
    width:auto;height:auto;padding:0;clip-path:none;background:none;color:inherit;
    box-shadow:none;font:inherit;letter-spacing:inherit}
}
/* over the text, the button waits while the card in the text is on screen */
@media (width > 1000px) and (max-width:1279px){
  :root:not([data-side="closed"]):not([data-tocpanel]) .docpage .tocbtn:not(.is-on){
    opacity:0;visibility:hidden}
}
@media (width > 1000px) and (max-width:1099px){
  [data-side="closed"]:not([data-tocpanel]) .docpage .tocbtn:not(.is-on){opacity:0;visibility:hidden}
}
/* in the margin: from 1424px with the site's column open, from 1240px with
   it folded, the margin holds a 200px list with 32px between it and the text */
@media (min-width:1424px){""" + _MARGIN.replace("%P%", "") + """}
@media (min-width:1240px){""" + _MARGIN.replace("%P%", '[data-side="closed"]') + """}
/* and, smaller, in a narrower margin (_COMPACT): from 1280px with the column
   open, from 1100px with it folded */
@media (min-width:1280px) and (max-width:1423px){""" + (_MARGIN + _COMPACT).replace(
    "%P%", ':root:not([data-side="closed"])') + """}
@media (min-width:1100px) and (max-width:1239px){""" + (_MARGIN + _COMPACT).replace(
    "%P%", '[data-side="closed"]') + """}

/* a phone or a tablet: the list stays in the text, and the pill brings it
   back as a sheet from the foot of the screen, but only while the reader is
   going back up the page: reading down, nothing covers the text */
@media (max-width:1000px){
  .docpage{padding-inline:22px}
  .foot.foot--doc{max-width:calc(var(--measure-doc) + 44px)}
  [data-toc] .docpage.has-toc>.tocdock{display:contents}
  [data-toc] .docpage.has-toc>.tocscrim{display:block;position:fixed;inset:0;z-index:45;
    background:rgba(39,34,28,.24);opacity:0;visibility:hidden;
    transition:opacity var(--t-fast) var(--ease-in-out),visibility 0s linear var(--t-fast)}
  [data-tocpanel] .docpage.has-toc>.tocscrim{opacity:1;visibility:visible;
    transition:opacity var(--t-mid) var(--ease)}
  .docpage .tocbtn{position:fixed;right:16px;bottom:calc(16px + env(safe-area-inset-bottom));
    z-index:20;min-height:44px;padding:0 18px 0 14px;border:1px solid var(--line);
    background:var(--page);background:color-mix(in oklab,var(--page) 86%,transparent);
    -webkit-backdrop-filter:saturate(1.3) blur(14px);backdrop-filter:saturate(1.3) blur(14px);
    box-shadow:var(--sh-2);opacity:0;visibility:hidden;transform:translateY(8px);
    transition:opacity var(--t-fast) var(--ease),transform var(--spring-fast),
      visibility 0s linear var(--t-fast),background-color var(--t-fast) var(--ease-state)}
  .docpage .tocbtn.is-on{opacity:1;visibility:visible;transform:none;
    transition:opacity var(--t-mid) var(--ease),transform var(--spring-mid),
      background-color var(--t-fast) var(--ease-state)}
  .docpage .tocbtn__t{position:static;width:auto;height:auto;clip-path:none;overflow:visible}
  .docpage .tocpanel{position:fixed;left:0;right:0;bottom:0;z-index:46;max-height:min(76vh,640px);
    padding:0 12px calc(20px + env(safe-area-inset-bottom)) 4px;background:var(--page);
    border-radius:var(--r-lg) var(--r-lg) 0 0;box-shadow:var(--sh-3);
    transform:translateY(100%);visibility:hidden;
    transition:transform var(--t-fast) var(--ease-in-out),visibility 0s linear var(--t-fast)}
  [data-tocpanel] .docpage .tocpanel{transform:none;visibility:visible;
    transition:transform var(--spring-mid)}
  .docpage .tocpanel{--tm:12px}
}
@media (max-width:1000px) and (prefers-reduced-motion:no-preference){
  .docpage .tocbtn.is-on:active{transform:scale(.97)}
}
@media (max-width:1000px) and (prefers-reduced-transparency:reduce){
  .docpage .tocbtn{background:var(--page);-webkit-backdrop-filter:none;backdrop-filter:none}
}

/* ---------- the body: his text in the column ---------- */
.docpage .doc>*{max-width:none}
.docpage .doc h2,.docpage .doc h3{scroll-margin-top:24px}
.docpage :is(h1,h2,h3,h4){font-variant-numeric:lining-nums proportional-nums}
.docpage .doc :is(h2,h3,h4) strong{font-weight:inherit}
.docpage .doc .hn{color:var(--muted)}
.docpage .doc :is(sub,sup){font-size:.75em;line-height:0}   /* the line keeps its height */
.docpage .doc .a-center{text-align:center}
.docpage .doc .a-right{text-align:right}
.docpage .doc li{margin:.45em 0}
.docpage .doc li>p{margin:0}
.docpage .doc li>p+p{margin-top:.5em}
.docpage .doc li::marker{color:var(--muted)}
.docpage .doc ol>li::marker{font-variant-numeric:lining-nums tabular-nums}

/* his colour, mapped onto the palette rather than carried raw; a paragraph he
   set wholly in italic is upright in the quieter ink (no italic is loaded) */
.docpage .ink-a{color:var(--accent)}
.docpage .ink-b{color:var(--nav)}
/* his navy words: the column's navy is lost on the dark page, the link blue keeps them blue */
:root[data-theme="dark"] .docpage .ink-b{color:var(--link)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .docpage .ink-b{color:var(--link)}}
.docpage .ink-m,.docpage .doc .p-it{color:var(--muted)}
.docpage .doc u:has(>strong){text-decoration:none}

.docpage .doc .docrule{margin:48px 0;border:0;border-top:1px solid var(--line)}

/* ---------- figures: the column's width at most, never past their pixels ---------- */
.docpage .doc figure{margin:40px 0}
/* beside a heading the heading's margins rule: a block above an h3 leaves the
   h3's 34px (not its own 40px), and a block right under a heading closes up to
   it, so the heading sits with what it introduces (at most 2.5:1) */
.docpage .doc>:is(figure,.tbl,.tfig,.callout,.flow,.figrow):has(+h3){margin-bottom:34px}
.docpage .doc>:is(h2,h3)+:is(figure,.tbl,.tfig,.callout,.flow,.figrow){margin-top:0}
/* His figures are drawn on white. On the page's warm paper a white box with
   a hairline round it read as a card laid on the page (the client, 26 Sep
   2026: "ayrık"), so a figure is multiplied into the paper instead: its white
   becomes the page's own colour, its ink stays ink, and nothing frames it.
   On the dark theme a multiply would sink it, so there it keeps its white
   and its corners. */
.docpage .doc figure img{display:block;max-width:100%;height:auto;margin-inline:auto;
  border:0;border-radius:0;mix-blend-mode:multiply}
/* a picture he set narrower than his column in Word keeps its share of this
   one (build.py writes it, 60% at least), centred, never past its pixels;
   on a phone every picture takes the column */
.docpage .doc figure.fig--inset{width:var(--inset);max-width:min(100%,var(--nat));
  margin-inline:auto}
.docpage .doc figure.fig--inset img{width:100%}
/* a picture smaller than the column: one track as wide as the picture (360px
   at least) centred in the column, so the picture centres on the text above
   and below it and its caption keeps to the track (contain keeps the caption
   from widening it) */
.docpage .doc>figure:not([class]){display:grid;
  grid-template-columns:minmax(min(100%,360px),max-content);justify-content:center}
.docpage figcaption{margin:12px 0 0;contain:inline-size;
  font-size:16px;line-height:1.5;color:var(--muted);text-wrap:pretty}
.docpage .fign{font-weight:600;color:var(--ink);font-variant-numeric:lining-nums}
/* drawn smaller than it is: the picture links to its full file. A pointer
   sees the zoom cursor; a touch screen, which has none, sees a mark under
   the picture's right corner, beside the caption's first line, which keeps
   clear of it. Laid over the picture it hid part of 39 of the 72 diagrams
   in one corner or another (a legend, a title, a coloured box) */
.docpage .figzoom{position:relative;display:block;border-radius:var(--r-md);cursor:zoom-in}
.docpage .figzoom__mark{position:absolute;right:0;top:calc(100% + 8px);display:none;
  place-items:center;width:32px;height:32px;border-radius:var(--r-pill);color:var(--muted);
  background:var(--page);box-shadow:0 0 0 1px var(--line)}
.docpage .figzoom__mark svg{display:block}
@media (hover:none){
  .docpage .figzoom__mark{display:grid}
  .docpage .fig--zoom>figcaption{padding-right:44px}
}
/* a picture set in a sentence, drawn in the line at the size of its words: an
   equation, whose glyphs fill 89% of its height */
.docpage .doc img.eq{display:inline-block;height:1.12em;width:auto;max-width:none;
  margin:0 .12em;vertical-align:-.28em;border:0;border-radius:0}
/* his animated figures (preview.py): the frame is the column's width at his
   canvas's ratio (inline), so the canvas fills it with nothing to scroll, and
   like a picture it is multiplied into the paper, its white the page's. The
   picture it redraws stands in where the frame cannot run, with no script,
   and on paper */
.docpage :is(.doc,.dochead) .anim{display:none}
.js .docpage :is(.doc,.dochead) .anim{display:block;width:100%;height:auto;border:0;
  border-radius:0;mix-blend-mode:multiply;color-scheme:light}
/* the dark theme: figures keep their white, with corners, as on paper */
:root[data-theme="dark"] .docpage .doc figure img,
:root[data-theme="dark"].js .docpage :is(.doc,.dochead) .anim{mix-blend-mode:normal;border-radius:var(--r-md)}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]) .docpage .doc figure img,
  :root:not([data-theme="light"]).js .docpage :is(.doc,.dochead) .anim{mix-blend-mode:normal;border-radius:var(--r-md)}
}
.js .docpage :is(.doc,.dochead) .anim__still{display:none}

/* The row of buttons under a moving figure (preview.py BAR, the script
   below): play or pause and restart, which drive the frame over postMessage
   (tools/numfig/engine.js, HOSTED), and full screen. It sits under the
   frame's right corner, beside the caption's first line, which flows round
   it, as the zoom mark sits under a still picture (above). Laid over the
   frame, the buttons hid type in 16 of the machine learning guide's 33
   figures on a laptop and 27 on a phone, and took the clicks meant for the
   figures' own controls in their corners.

   Full screen: four corners that open a little under the pointer; the figure
   then fills the screen: the frame as large as the screen allows at its own
   ratio (--ar) with the row under it, drawn again at that size, since every
   figure draws its lines and type afresh when its frame changes size. Where
   the browser cannot give an element the screen (a phone's Safari), the
   figure lies over the page instead. */
.docpage .fig--anim{position:relative}
/* a picture redrawn as several moving figures (preview.py _animated_parts):
   each its own frame and row, one under the other, the caption under all */
.docpage .fig--parts>.fig--anim+.fig--anim{margin-top:28px}
.anim__bar{display:none}
.js .docpage .fig--anim>.anim__bar{display:flex;gap:8px;float:right;margin:10px 0 4px 16px}
/* the float stays in its figure: a cover, a one-line caption, a part */
.js .docpage .fig--anim:not(.fig--cell,:fullscreen,.is-full){display:flow-root}
.js .docpage .tbl .fig--cell>.anim__bar{grid-area:2/1;float:none;justify-self:end;width:auto;margin:6px 0 0}
.anim__bar>button{position:relative;display:grid;place-items:center;box-sizing:border-box;width:32px;height:32px;
  margin:0;padding:0;border-radius:50%;border:1px solid var(--line);background:var(--page);color:var(--muted);
  cursor:pointer;-webkit-tap-highlight-color:transparent}
.anim__bar>button[hidden]{display:none}
.anim__bar svg{display:block;width:16px;height:16px;overflow:visible}
.js .docpage .fig--anim:is(:hover,:focus-within) .anim__bar>button{color:var(--ink);border-color:var(--line-strong)}
@media (hover:hover){.anim__bar>button:hover{background:var(--surface)}}
.anim__bar>button:active{background:var(--line)}
.anim__bar>button:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
/* a finger gets 44px: the gap and a ring round each button take it */
@media (pointer:coarse){.js .docpage .fig--anim>.anim__bar{gap:12px}
  .anim__bar>button::before{content:'';position:absolute;inset:-6px;border-radius:50%}}
@media (prefers-reduced-motion:no-preference){
  .anim__bar>button{transition:color var(--t-quick) var(--ease-state),border-color var(--t-quick) var(--ease-state),
    background-color var(--t-quick) var(--ease-state),transform var(--spring-fast)}
  .anim__bar>button:active{transform:scale(.94)}}
.anim__full .af-shut{display:none}
.anim__full .af-open path{transition:transform var(--spring-fast)}
@media (hover:hover) and (prefers-reduced-motion:no-preference){
  .anim__full:hover .af-a{transform:translate(-1.5px,-1.5px)}
  .anim__full:hover .af-b{transform:translate(1.5px,-1.5px)}
  .anim__full:hover .af-c{transform:translate(-1.5px,1.5px)}
  .anim__full:hover .af-d{transform:translate(1.5px,1.5px)}
}
/* full screen is the figure alone, as large as the screen allows with its
   row under it: its number and caption stay on the page, and its white still
   melts into the paper (the blend above) so no frame edge shows */
.docpage .fig--anim:is(:fullscreen,.is-full){--pad:clamp(12px,2.5vw,40px);display:flex;flex-direction:column;
  align-items:center;justify-content:center;width:auto;max-width:none;margin:0;padding:var(--pad);
  background:var(--page);overflow:hidden}
/* as the browser's own :fullscreen{margin:0 !important}: no figure margin rule wins */
.docpage .fig--anim.is-full{position:fixed;inset:0;z-index:1000;margin:0!important}
.js .docpage .fig--anim:is(:fullscreen,.is-full) .anim{display:block;flex:none;
  width:min(100%,calc((100vh - 2 * var(--pad) - 42px) * var(--ar,1.6)));
  width:min(100%,calc((100dvh - 2 * var(--pad) - 42px) * var(--ar,1.6)));height:auto;
  opacity:1;visibility:visible;transform:none}
.js .docpage .fig--anim:is(:fullscreen,.is-full) .anim__still{display:none}
.docpage .fig--anim:is(:fullscreen,.is-full) figcaption{display:none}
.docpage .fig--anim:is(:fullscreen,.is-full)>.anim__bar{float:none;justify-content:flex-end;margin:10px 0 0;
  width:min(100%,calc((100vh - 2 * var(--pad) - 42px) * var(--ar,1.6)));
  width:min(100%,calc((100dvh - 2 * var(--pad) - 42px) * var(--ar,1.6)))}
.docpage .fig--anim:is(:fullscreen,.is-full) .af-open{display:none}
.docpage .fig--anim:is(:fullscreen,.is-full) .af-shut{display:inline}
/* the page's stable gutter is let go too, or the figure stops 15px short of the edge */
.fig-open{overflow:hidden;scrollbar-gutter:auto}
@media print{.anim__bar{display:none!important}}

/* rows of book covers he set side by side, captioned "Left to right": one
   height across the row (build.py sets the row's width from it), each cover
   the share of the row its proportions ask for */
.docpage .doc .figrow{margin:32px 0 40px}
.docpage .figrow__row{--gap:20px;display:flex;justify-content:center;align-items:flex-start;
  gap:var(--gap);max-width:calc(var(--rw) + var(--gaps) * var(--gap));margin-inline:auto}
.docpage .doc .figrow__row figure{flex:1 1 0%;min-width:0;margin:0}
.docpage .doc .figrow__row img{width:100%}
.docpage .figrow figcaption{margin:14px auto 0;text-align:center}

/* ---------- tables: set as a book sets them ---------- */
/* A rule in ink over the table, a hairline under its column heads and
   between its rows, none between columns, the caption under it. A table is
   the column's width; one that cannot fit scrolls inside it and the
   page-coloured cover slides off the edge that has more (a phone restacks
   every table but a small matrix, so only a tablet can meet one) */
.docpage .doc .tbl{max-width:none;margin:40px 0;overflow-x:auto;overscroll-behavior-x:contain;
  background:
    linear-gradient(to right,var(--page) 30%,transparent) left center/40px 100% no-repeat local,
    linear-gradient(to left,var(--page) 30%,transparent) right center/40px 100% no-repeat local,
    radial-gradient(farthest-side at 0 50%,color-mix(in oklab,var(--ink) 16%,transparent),
      transparent) left center/12px 100% no-repeat scroll,
    radial-gradient(farthest-side at 100% 50%,color-mix(in oklab,var(--ink) 16%,transparent),
      transparent) right center/12px 100% no-repeat scroll}
.docpage .doc>.tfig{max-width:none;margin:40px 0}
.docpage .doc .tfig .tbl{margin:0}
.docpage .tbl{--gut:20px;--pad:13px}
.docpage .tbl table{width:100%;border-collapse:collapse;border-top:1px solid var(--ink);
  border-bottom:1px solid var(--line)}
.docpage .tbl :is(th,td){padding:var(--pad) var(--gut) var(--pad) 0;text-align:left;
  vertical-align:top;border:0;border-bottom:1px solid var(--rule)}
.docpage .tbl tr>:last-child{padding-right:0}
.docpage .tbl tbody tr:last-child>*{border-bottom:0}
/* the column heads, in the interface's voice (theme.py th), on the line
   their feet share */
.docpage .tbl thead :is(th,td){padding:12px var(--gut) 10px 0;border-bottom:1px solid var(--line);
  vertical-align:bottom;text-wrap:balance}
.docpage .tbl thead th:last-child{padding-right:0}
/* a row's name is the table's key: his words in the text's face, in ink;
   his bold stays bold */
.docpage .tbl th[scope=row]{font:400 15px/1.45 var(--serif);letter-spacing:0;
  text-transform:none;color:var(--ink);font-variant-numeric:lining-nums proportional-nums}
.docpage .tbl :is(td,th) p{margin:0 0 .5em;text-wrap:pretty}
.docpage .tbl :is(td,th) p:last-child{margin:0}
.docpage .tbl :is(td,th) :is(ul,ol){margin:.25em 0 .5em;padding-left:1.2em}
/* a column of ratings stays centred as he set it, and its heading with it;
   names and phrases read from their left edge (preview.py _column_align) */
.docpage .doc .tbl :is(td,th) p{text-align:inherit}
.docpage .tbl :is(td,th).c{text-align:center}
.docpage .tbl :is(td,th).c:not(:last-child){padding-inline:calc(var(--gut) / 2)}
/* a picture in a table is part of the table: no frame, the column's width
   at most and never past half its pixels; the words he set under it are its
   label */
.docpage .tbl figure{margin:2px 0 0}
.docpage .tbl figure img{border:0;border-radius:0;margin-inline:0}
.docpage .tbl .c figure img{margin-inline:auto}
.docpage .tbl figure+p{margin-top:6px;font-size:14px;line-height:1.35}
/* A picture redrawn as a moving figure (preview.py _in_cell): the frame and
   its still share one box. The still shows until the row is read; then the
   frame fades in over it and plays, and when the reader moves on it fades
   back to the still and waits off the page, where it neither plays nor takes
   focus (the script's is-live and is-ready). One row's figure moves at a
   time, the one being read. Reduced motion shows every frame, still, as a
   figure's is; paper and a page with no script show the still */
.docpage .tbl .fig--cell{display:grid;width:100%;margin-inline:auto}
.docpage .tbl .fig--cell>*{grid-area:1/1;width:100%;height:auto}
.js .docpage .tbl .fig--cell .anim__still{display:block;
  transition:opacity var(--t-mid) var(--ease-state)}
.js .docpage .tbl .fig--cell .anim{position:relative;z-index:1;opacity:0;visibility:hidden;
  transform:translateX(-300vw);
  transition:opacity var(--t-fast) var(--ease-state),visibility 0s linear var(--t-fast),
    transform 0s linear var(--t-fast)}
.js .docpage .tbl .is-live .fig--cell.is-ready .anim{opacity:1;visibility:visible;transform:none;
  transition:opacity var(--t-mid) var(--ease-state)}
.js .docpage .tbl .is-live .fig--cell.is-ready .anim__still{opacity:0}
/* the dark theme: the frame keeps its white and its corners, as its still
   does (multiplied into the dark page it went black) */
:root[data-theme="dark"].js .docpage .tbl .fig--cell .anim{mix-blend-mode:normal;
  border-radius:var(--r-md)}
@media (prefers-reduced-motion:reduce){
  .js .docpage .tbl .fig--cell .anim{opacity:1;visibility:visible;transform:none;transition:none}
  .js .docpage .tbl .fig--cell .anim__still{display:none}
}
/* a table's figure full screen is the figure's full screen (above): the cell's
   rules, which park the frame off the page and show its still, come later
   and as strong, so these, one class stronger, take them back */
.js .docpage .tbl .fig--cell:is(:fullscreen,.is-full){display:flex}
.js .docpage .tbl .fig--cell:is(:fullscreen,.is-full) .anim{opacity:1;visibility:visible;transform:none;
  transition:none;width:min(100%,calc((100vh - 2 * var(--pad) - 42px) * var(--ar,1.6)));
  width:min(100%,calc((100dvh - 2 * var(--pad) - 42px) * var(--ar,1.6)))}
.js .docpage .tbl .fig--cell:is(:fullscreen,.is-full) .anim__still{display:none}
.js .docpage .tbl .fig--cell:is(:fullscreen,.is-full)>.anim__bar{margin:10px 0 0;
  width:min(100%,calc((100vh - 2 * var(--pad) - 42px) * var(--ar,1.6)));
  width:min(100%,calc((100dvh - 2 * var(--pad) - 42px) * var(--ar,1.6)))}
.docpage .tbl .tr-span td{padding-top:16px;padding-bottom:16px}
/* more of a group (preview.py tr-same): no rule inside it, and the name it
   repeats in the quieter ink */
.docpage .tbl tr:has(+.tr-same)>*{border-bottom-color:transparent}
.docpage .tbl .tr-same>th[scope=row]{color:var(--muted)}
.docpage .tfig figcaption{margin-top:12px}
/* five columns and more: a step smaller, and closer, so they fit the column.
   Seven (the ML guide's Table 1) is a step smaller again: its narrowest
   possible layout was 714px at 14px, bound by single words ("labels/
   threshold)", the heading INTERPRETABILITY), and at 13px it fits 672 */
.docpage .tbl--many{--gut:10px}
.docpage .tbl--many :is(td,th){font-size:14px}
.docpage .tbl--many thead th{letter-spacing:.03em}
.docpage .tbl--dense{--gut:8px;--pad:11px}
.docpage .tbl--dense :is(td,th){font-size:13px}
.docpage .tbl--dense thead th{font-size:11px;letter-spacing:.02em}
.docpage .tbl--dense th[scope=row]{font-size:14px}
/* Signal Processing's notes (preview.py tbl--notes): each row's note sits
   under its values, across the columns after its name, in the quieter ink of
   a note; its column's head sits the same way under the others. The rule
   between rows is the row's own */
@media (min-width:641px){
  .docpage .tbl--notes :is(table,thead,tbody){display:block}
  .docpage .tbl--notes tr{display:grid;column-gap:var(--gut);
    grid-template-columns:minmax(0,1.3fr) minmax(0,1fr) minmax(0,1.15fr) minmax(0,1fr);
    padding:var(--pad) 0;border-bottom:1px solid var(--rule)}
  .docpage .tbl--notes tbody tr:last-child{border-bottom:0}
  .docpage .tbl--notes thead tr{padding:12px 0 10px;border-bottom:1px solid var(--line)}
  .docpage .tbl--notes :is(thead,tbody) tr>:is(th,td),.docpage .tbl--notes tr>.c:not(:last-child){
    padding:0;border:0}
  .docpage .tbl--notes thead tr>:not(:last-child){align-self:end}
  .docpage .tbl--notes tbody tr>:first-child{grid-row:1 / span 2}
  .docpage .tbl--notes tr>:last-child{grid-column:2 / -1;margin-top:6px}
  .docpage .tbl--notes tbody tr>:last-child{font-size:14px;line-height:1.45;color:var(--muted)}
}
/* A picture and his words about it (preview.py tbl--fig: the waves guide's
   fun table): the picture in a column of its own at the left, a third of
   the table (228px, where Word's three columns left it 165), its label under
   it; the row's name over his words as their heading, and the words in a
   measure that reads (58 characters a line, where a third column left them
   45). The column heads sit the same way */
@media (min-width:641px){
  .docpage .tbl--fig :is(table,thead,tbody){display:block}
  .docpage .tbl--fig colgroup{display:none}
  .docpage .tbl--fig tr{display:grid;grid-template-columns:minmax(0,34%) minmax(0,1fr);
    column-gap:28px;padding:18px 0;border-bottom:1px solid var(--rule)}
  .docpage .tbl--fig tbody tr:last-child{border-bottom:0}
  .docpage .tbl--fig thead tr{row-gap:2px;padding:12px 0 10px;border-bottom:1px solid var(--line)}
  .docpage .tbl--fig :is(thead,tbody) tr>:is(th,td){grid-column:2;padding:0;border:0}
  .docpage .tbl--fig :is(thead,tbody) tr>.pic{grid-column:1;grid-row:1 / span 2}
  .docpage .tbl--fig thead tr>.pic{align-self:end}
  .docpage .tbl--fig tbody th[scope=row]{font-size:16px;line-height:1.35}
  .docpage .tbl--fig tbody tr>td:not(.pic){margin-top:6px}
}

/* ---------- a row of steps with his arrows between ---------- */
/* Two rows for every step, as subgrids: pictures of four heights centre on one
   line and the four labels start on the next. Every step takes an equal share
   of the row and every arrow its own width, so each arrow sits halfway between
   the two pictures it joins. The pictures keep their transparent ground and
   take no frame, drawn at half their pixels */
.docpage .doc .flow{--flow-arrow:40px;--flow-gap:12px;display:grid;grid-auto-flow:column;
  grid-template-rows:auto auto;grid-auto-columns:minmax(0,1fr) auto;align-items:center;
  column-gap:var(--flow-gap);max-width:none;margin:40px 0}
.docpage .flow__step{min-width:0;text-align:center}
.docpage .doc .flow__step{grid-row:1/3;display:grid;grid-template-rows:subgrid;row-gap:0;
  grid-template-columns:minmax(0,1fr);justify-items:center}
.docpage .doc .flow__arrow{grid-row:1}
.docpage .doc .flow__step figure{width:auto;min-width:0;margin:0 auto 10px;align-self:center}
.docpage .doc .flow__step img{border:0;border-radius:0;margin-inline:auto}
/* a label may take the free half of the gap under the arrow beside it, so a
   short one keeps to one line; a longer one wraps */
.docpage .flow__step p{margin:0;font-size:15px;line-height:1.35;align-self:start;
  width:max-content;max-width:calc(100% + var(--flow-arrow) + var(--flow-gap))}
/* his steps redrawn as moving figures (preview.py _in_cell, tools/numfig/hw_*.py):
   each frame keeps his picture's size, which preview.py writes on it, and an
   icon takes no full screen button */
.docpage .doc .flow__step .fig--anim{max-width:100%}
.js .docpage .doc .flow__step .anim__bar{display:none}
/* his arrows as the figures draw theirs (engine.js arrow()): a hairline with a
   TikZ stealth tip, in the muted ink. The glyph he typed stays in the page,
   silent (aria-hidden) and unseen. The margin under it is the pictures', so it
   sits on their middle */
.docpage .flow__arrow{position:relative;flex:none;width:var(--flow-arrow,40px);height:11px;margin-bottom:10px;
  font-size:0;line-height:0;color:var(--muted)}
.docpage .flow__arrow::before,.docpage .flow__arrow::after{content:"";position:absolute;
  background:currentColor}
.docpage .flow__arrow::before{left:0;right:4px;top:5px;height:1px;transform-origin:0 50%}
.docpage .flow__arrow::after{right:0;top:2.9px;width:6.5px;height:5.2px;
  clip-path:polygon(100% 50%,0 0,33.2% 50%,0 100%)}
/* An arrow draws itself once the icon before it is down: the figure marks it
   is-wait while it waits off screen and is-in when its turn comes
   (tools/numfig/hw_lib.py), so each arrow draws after the step before it and
   before the next. The shaft draws from the step before on Motion's spring and
   the tip arrives 40ms behind it, as the site's own arrows do. On a screen, where
   motion is welcome; everywhere else the arrow is simply there */
@media screen and (prefers-reduced-motion:no-preference){
  .docpage .flow__arrow.is-wait::before{transform:scaleX(0)}
  .docpage .flow__arrow.is-wait::after{opacity:0}
  .docpage .flow__arrow.is-wait.is-in::before{transform:none;animation:flow-shaft var(--spring-fast) both}
  .docpage .flow__arrow.is-wait.is-in::after{opacity:1;
    animation:flow-tip var(--spring-fast) 40ms both,flow-tip-in var(--t-fast) var(--ease-state) 40ms both}
}
@keyframes flow-shaft{from{transform:scaleX(0)}}
@keyframes flow-tip{from{transform:translateX(-5px)}}
@keyframes flow-tip-in{from{opacity:0}}
/* A phone: the steps down the page, each picture in one column beside its
   label, and the arrows between the pictures, turned to point down */
@media (max-width:640px){
  .docpage .doc .flow{grid-auto-flow:row;grid-template-rows:none;
    grid-template-columns:auto minmax(0,1fr);grid-auto-columns:auto;column-gap:16px;row-gap:0}
  .docpage .doc .flow__step{grid-row:auto;grid-column:1/-1;grid-template-rows:none;
    grid-template-columns:subgrid;align-items:center;justify-items:start}
  .docpage .doc .flow__step figure{margin:0;justify-self:center}
  .docpage .doc .flow__step p{text-align:left;align-self:center;width:auto;max-width:none}
  .docpage .doc .flow__arrow{grid-row:auto;grid-column:1;justify-self:center;width:24px;
    margin:10px 0;transform:rotate(90deg)}
}

/* ---------- his asides: the fill says what it is, nothing else does ---------- */
.docpage .doc .callout{max-width:none;margin:40px 0;padding:24px 28px;background:var(--surface);
  border-radius:var(--r-md);font-size:18px;line-height:1.55}
.docpage .callout p{margin:0 0 .75em}
.docpage .callout>:last-child{margin-bottom:0}
.docpage .callout__t{font-weight:600;color:var(--ink)}
.docpage .callout h2.callout__t{font:600 18px/1.55 var(--serif);letter-spacing:0;margin:0;
  text-wrap:wrap}
.docpage .callout h2.callout__t:not(:last-child){margin-bottom:.75em}
.docpage .doc .callout--label{padding:14px 20px}
.docpage .callout figure{margin:16px 0}

/* ---------- notes ---------- */
.docpage .fnref{font-size:.72em;line-height:0;vertical-align:.45em;text-decoration:none;
  font-variant-numeric:lining-nums}
.docpage .doc>:not(.fn)+.fn{margin-top:48px;padding-top:24px;border-top:1px solid var(--rule)}
.docpage .fn{font-size:16px;line-height:1.5;color:var(--muted)}
.docpage .fn__back{text-decoration:none}

/* ---------- states: hover only where a pointer hovers ---------- */
/* a lit row takes one step of ink over what it sits on: the card in the
   text, the page in the dock */
@media (hover:hover){
  .docpage .crumb a:hover{color:var(--ink)}
  .docpage .toc--body :is(li>a,.toc__sum):hover{
    background:color-mix(in oklab,var(--ink) 5%,var(--card))}
  .docpage .toc--rail a:hover{background:color-mix(in oklab,var(--ink) 5%,var(--page))}
  .docpage .toc a:hover,.docpage .toc--body .toc__sum:hover::after,
  .docpage .toc__sum:hover .toc__chev{color:var(--ink)}
  /* muted is 4.20:1 on the lit card: what was muted steps to body (6.36:1) */
  .docpage .toc a:hover{--num:var(--body)}
  .docpage .toc__sum:hover .toc__n{color:var(--body)}
  .docpage .tocbtn:hover{background:color-mix(in oklab,var(--ink) 7%,var(--card))}
  .docpage .tocpanel__x:hover{background:color-mix(in oklab,var(--ink) 5%,var(--page));
    color:var(--ink)}
  .docpage .docdl:hover .docdl__t{text-decoration-color:currentColor}
}
.docpage .crumb a:focus-visible,.docpage .docdl:focus-visible,
.docpage .figzoom:focus-visible,.docpage .tbl:focus-visible,
.docpage .fnref:focus-visible,.docpage .fn__back:focus-visible,
.docpage :is(.tocbtn,.tocpanel__x):focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.docpage .tocpanel__x:focus-visible{color:var(--ink)}
.docpage .tocbtn:active{background:color-mix(in oklab,var(--ink) 11%,var(--card))}
.docpage .tocpanel__x:active{background:color-mix(in oklab,var(--ink) 8%,var(--page))}
/* the keyboard sees what the pointer sees, as on a Gallery row: the fill,
   and the ring inset so the card's or the list's own edge never clips it */
.docpage :is(.toc a,.toc__sum):focus-visible{outline:2px solid var(--focus);outline-offset:-2px;
  border-radius:var(--r-sm)}
.docpage .toc--body :is(li>a,.toc__sum):focus-visible{
  background:color-mix(in oklab,var(--ink) 5%,var(--card))}
.docpage .toc--rail a:focus-visible{background:color-mix(in oklab,var(--ink) 5%,var(--page))}
.docpage .toc a:focus-visible,.docpage .toc--body .toc__sum:focus-visible::after,
.docpage .toc__sum:focus-visible .toc__chev{color:var(--ink)}
.docpage .toc a:is(:focus-visible,:active){--num:var(--body)}
.docpage .toc__sum:is(:focus-visible,:active) .toc__n{color:var(--body)}
.docpage .toc--body :is(li>a,.toc__sum):active{
  background:color-mix(in oklab,var(--ink) 9%,var(--card))}
.docpage .toc--rail a:active{background:color-mix(in oklab,var(--ink) 8%,var(--page))}
/* the hairlines that touch a lit row in the card fade out. Only :has()
   selectors, each rule alone, so a browser without :has() drops just these;
   forced colours paint no fill, so there hover and press keep the lines */
@media (hover:hover) and (forced-colors:none){
  .docpage .toc--body li:has(>a:hover)::before,
  .docpage .toc--body li:has(>a:hover)+li::before{opacity:0}
}
@media (forced-colors:none){
  .docpage .toc--body li:has(>a:active)::before,
  .docpage .toc--body li:has(>a:active)+li::before{opacity:0}
}
.docpage .toc--body li:has(>a:focus-visible)::before,
.docpage .toc--body li:has(>a:focus-visible)+li::before{opacity:0}
.docpage .docdl:focus-visible .docdl__t{text-decoration-color:currentColor}

/* ---------- narrow ---------- */
@media (max-width:1000px){
  /* build.py's scroll-padding-top keeps a jumped-to heading clear of the sticky
     bar; this is the air above it, as on a wide screen */
  .docpage .doc h2,.docpage .doc h3,.docpage .toc--body{scroll-margin-top:24px}
}
@media (max-width:640px){
  .docpage .dochead figure{margin-bottom:28px}
  .docpage .dochead__dek{font-size:19px}
  .docpage .doc .callout{padding:20px}
  .docpage .doc>:is(figure,.tbl,.tfig,.callout,.flow){margin:32px 0}
  .docpage .crumb{margin-top:-22px}
  /* every picture takes the column on a phone, its share set aside */
  .docpage .doc figure.fig--inset{width:auto}
  /* the brief's h1 was set for a name; a 121-character title at 32px runs to
     eight lines on a 320px phone */
  .docpage .dochead--long h1{font-size:clamp(24px,3.6vw + 12px,32px);line-height:1.16}
  /* and the section heads step down under it: h1 24 to 32px, h2 22, h3 20 */
  .docpage .doc h2{font-size:22px}
  .docpage .doc h3{font-size:20px}
  /* a small matrix keeps its grid, and its row names stay if it must scroll */
  .docpage .tbl.tbl--scroll :is(td,th){padding-right:12px}
  .docpage .tbl--scroll th[scope=row]{position:sticky;left:0;z-index:1;background:var(--page);
    box-shadow:1px 0 0 var(--rule)}
}
@media (max-width:640px){""" + _STACK.replace("%T%", ".tbl--stack") + """}
/* the ML guide's Table 1, seven columns, is 637px at its narrowest: on a
   screen under 681px it restacks as it does on a phone */
@media (min-width:641px) and (max-width:700px){""" + _STACK.replace("%T%", ".tbl--stack.tbl--dense") + """}
@media (max-width:560px){
  .docpage .figrow__row{--gap:12px}
}

@media print{
  .docpage .tocdock,.docpage .tocscrim,.docpage .crumb,.docpage .figzoom__mark{
    display:none!important}
  .docpage.has-toc .toc--body{display:block!important;background:none;border-color:var(--line)}
  .docpage .toc__chev,.docpage .toc__n,.docpage .toc--body .toc__sum::after,
  .docpage .toc--body li>a::after{display:none}
  .docpage .toc__fold>ol{opacity:1!important}
  .docpage figure,.docpage .callout,.docpage .tbl tr{break-inside:avoid}
  .docpage .tbl{overflow:visible;background:none}
  .docpage .tbl :is(thead,thead tr){break-after:avoid}
  .docpage .tbl .fig--cell .anim__still{display:block!important;opacity:1!important}
  .js .docpage :is(.doc,.dochead) .anim{display:none}
  .js .docpage :is(.doc,.dochead) .anim__still{display:block}
}
@media print{
  .docpage .toc__fold::details-content{content-visibility:visible!important}
}
/* How far through the document the reader is: a hairline in the accent along
   the top of the page's column that grows as the page scrolls (a
   scroll-driven animation: the reader's own scroll moves it, so it moves for
   every reader; nothing where the browser has none). On a phone it runs
   under the bar. */
@supports (animation-timeline:scroll()){
  .docpage::before{content:"";position:fixed;z-index:31;top:0;left:var(--side-now);right:0;height:2px;
    background:var(--accent);transform-origin:0 50%;transform:scaleX(0);pointer-events:none;
    animation:doc-read linear both;animation-timeline:scroll(root)}
  @media (max-width:1000px){.docpage::before{left:0;top:59px}}
}
@keyframes doc-read{to{transform:scaleX(1)}}
@media print{.docpage::before{display:none}}
"""

# The dock. `laid` is where the list lies, read off the stylesheet rather than
# worked out again here: in the margin its position is static, over the text
# or as a sheet it is fixed. In the margin its state is the reader's
# (data-toc on <html>, stored); over the text it is only ever asked for
# (data-tocpanel, never stored, gone when the width changes). The script marks
# the section being read, in the dock's list and, by its chapter, in the card
# in the text; opens the list scrolled to it; and moves focus in and out. The
# button shows while the card in the text is off screen: below it, before the
# reader reaches it, and above it, once they have passed it. On a phone or a
# tablet the pill floats over the text, so after the card it comes back only
# while the reader goes back up the page.
JS = """
/* his animated figures: the picture each redraws is printed in its place, so
   it loads before the page goes to paper, not only as it nears the screen.
   Chrome takes the print before an image asked for at beforeprint arrives, so
   every lazy picture of the document (the stills, hidden on screen, and his
   pictures) loads once the page has, in idle time and at low priority, unless
   the reader asked to save data; beforeprint stays as the last resort */
addEventListener('beforeprint',function(){
  [].forEach.call(document.querySelectorAll('.docpage .anim__still'),function(i){i.loading='eager';});});
addEventListener('load',function(){
  if(navigator.connection&&navigator.connection.saveData)return;
  function all(){[].forEach.call(document.querySelectorAll('.docpage img[loading=lazy]'),function(i){
    i.fetchPriority='low';i.loading='eager';});}
  if(window.requestIdleCallback)requestIdleCallback(all,{timeout:4000});else setTimeout(all,2000);});
/* a table's moving figures (preview.py _in_cell): only the row being read
   plays. A row is read while it crosses a line two fifths down the screen.
   Its frames load as it comes within a screen of the view, fade in over their
   stills once loaded, and when the reader moves on fade back and wait off the
   page, paused and out of the tab order. With less motion asked for, the
   stylesheet shows every frame, still */
(function(){
  var figs=document.querySelectorAll('.docpage .tbl .fig--cell');
  if(!figs.length||!window.IntersectionObserver||matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  var rows=[],seen=[],live=null;
  function frames(tr,f){[].forEach.call(tr.querySelectorAll('.fig--cell iframe'),f);}
  [].forEach.call(figs,function(fig){
    var tr=fig.closest('tr'),fr=fig.querySelector('iframe');
    function ready(){fig.classList.add('is-ready');}
    fr.inert=true;fr.addEventListener('load',ready);
    try{if(fr.contentDocument.readyState==='complete'&&fr.contentWindow.location.href!=='about:blank')ready();}catch(e){}
    if(rows.indexOf(tr)<0)rows.push(tr);});
  var near=new IntersectionObserver(function(es){es.forEach(function(e){
    if(!e.isIntersecting)return;near.unobserve(e.target);
    frames(e.target,function(i){i.loading='eager';});});},{rootMargin:'100% 0px'});
  var band=new IntersectionObserver(function(es){
    es.forEach(function(e){var k=seen.indexOf(e.target);
      if(e.isIntersecting){if(k<0)seen.push(e.target);}else if(k>=0)seen.splice(k,1);});
    var next=null;
    for(var i=0;i<rows.length&&!next;i++)if(seen.indexOf(rows[i])>=0)next=rows[i];
    if(next===live)return;
    if(live){live.classList.remove('is-live');frames(live,function(f){f.inert=true;});}
    live=next;
    if(live){live.classList.add('is-live');frames(live,function(f){f.inert=false;});}
  },{rootMargin:'-40% 0px -59% 0px'});
  rows.forEach(function(tr){near.observe(tr);band.observe(tr);});
})();
/* the card's fold: opened by the reader, its rows fade in and settle; the
   height is already theirs, so the page under it moves once */
var fold=document.querySelector('.docpage .toc__fold');
if(fold&&fold.animate)fold.querySelector('summary').addEventListener('click',function(){
  if(fold.open||matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  fold.lastElementChild.animate([{opacity:0,transform:'translateY(-4px)'},{opacity:1,transform:'none'}],
    {duration:200,easing:'cubic-bezier(.2,.8,.2,1)'});
});
/* a moving figure, full screen: the browser's own full screen where it can
   give it to an element, else the figure laid over the page; Escape, the
   button again, or the browser's own way out bring it back. The frame's ratio
   (its inline aspect-ratio) sizes it on the screen (CSS --ar). */
(function(){
  var figs=[].slice.call(document.querySelectorAll('.docpage .fig--anim'));if(!figs.length)return;
  var real=!!(document.fullscreenEnabled&&Element.prototype.requestFullscreen),over=null;
  function said(f,on){var b=f.querySelector('.anim__full');
    if(b)b.setAttribute('aria-label',on?'Leave full screen':'Show this figure full screen');}
  /* a table's frame goes back to sleep unless its row is the one being read */
  function rest(f){var tr=f.closest('tr');
    if(f.classList.contains('fig--cell')&&tr&&!tr.classList.contains('is-live')){
      var fr=f.querySelector('iframe.anim');if(fr)fr.inert=true;}}
  document.addEventListener('fullscreenchange',function(){
    figs.forEach(function(f){if(document.fullscreenElement!==f)rest(f);});});
  function shut(){if(!over)return;var f=over;over=null;f.classList.remove('is-full');rest(f);
    document.documentElement.classList.remove('fig-open');said(f,false);
    var b=f.querySelector('.anim__full');if(b)b.focus({preventScroll:true});}
  figs.forEach(function(f){
    var fr=f.querySelector('iframe.anim'),b=f.querySelector('.anim__full');if(!fr||!b)return;
    var r=(fr.style.aspectRatio||'').split('/');
    if(r.length===2&&+r[1])f.style.setProperty('--ar',(+r[0])/(+r[1]));
    b.addEventListener('click',function(e){e.stopPropagation();
      if(document.fullscreenElement===f){document.exitFullscreen();return}
      if(over===f){shut();return}
      if(fr.loading==='lazy')fr.loading='eager';
      if(f.classList.contains('fig--cell'))fr.inert=false;
      /* a phone held upright turns the figure on its side where it may, so it
         takes the long side of the screen; leaving full screen lets it go */
      /* the page stops scrolling first, so its scrollbar is gone before the
         browser sizes the figure to the screen, and no strip is left beside it */
      if(real){document.documentElement.classList.add('fig-open');
        f.requestFullscreen().then(function(){
        var o=screen.orientation;
        if(o&&o.lock&&innerWidth<innerHeight&&(+(f.style.getPropertyValue('--ar'))||1)>1)o.lock('landscape').catch(function(){});
      }).catch(function(){over=f;f.classList.add('is-full');said(f,true)});}
      else{over=f;f.classList.add('is-full');document.documentElement.classList.add('fig-open');said(f,true)}});
  });
  /* the row's play or pause and restart drive the frame (tools/numfig/engine.js,
     HOSTED) and show once it answers; a frame that plays once says so, and
     keeps them hidden (preview.py BAR) */
  var PLAY='<svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true" focusable="false"><path d="M5.2 3.4v9.2c0 .5.5.8.9.5l7.1-4.6c.4-.2.4-.8 0-1L6.1 2.9c-.4-.3-.9 0-.9.5z"/></svg>',
    PAUSE='<svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true" focusable="false"><rect x="4.2" y="3.2" width="2.5" height="9.6" rx=".7"/><rect x="9.3" y="3.2" width="2.5" height="9.6" rx=".7"/></svg>';
  figs.forEach(function(f){
    var fr=f.querySelector('iframe.anim'),bar=f.querySelector('.anim__bar');if(!fr||!bar)return;
    var pp=bar.querySelector('.anim__pp'),rs=bar.querySelector('.anim__rs');if(!pp||!rs)return;
    function send(m){try{fr.contentWindow.postMessage(m,location.origin)}catch(e){}}
    pp.addEventListener('click',function(e){e.stopPropagation();send({nf:'toggle'})});
    rs.addEventListener('click',function(e){e.stopPropagation();send({nf:'restart'})});
    addEventListener('message',function(e){var m=e.data;
      if(e.source!==fr.contentWindow||e.origin!==location.origin||!m||m.nf!=='state')return;
      pp.hidden=rs.hidden=!!m.quiet;pp.innerHTML=m.playing?PAUSE:PLAY;
      pp.setAttribute('aria-label',m.playing?'Pause animation':'Play animation')});
    send({nf:'hello'});fr.addEventListener('load',function(){send({nf:'hello'})});
  });
  document.addEventListener('fullscreenchange',function(){
    if(!document.fullscreenElement&&!over)document.documentElement.classList.remove('fig-open');
    figs.forEach(function(f){said(f,document.fullscreenElement===f)})});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&over)shut()});
})();
var page=document.querySelector('.docpage.has-toc'),root=document.documentElement;
if(!page||!root.hasAttribute('data-toc'))return;
var btn=page.querySelector('.tocbtn'),panel=page.querySelector('.tocpanel'),K='wad:toc',
  list=page.querySelector('#contents'),mark=panel.querySelector('.toc__mark'),
  links=[].slice.call(panel.querySelectorAll('a[href^="#"]')),
  heads=links.map(function(a){return document.getElementById(a.hash.slice(1));}),
  PH=matchMedia('(max-width: 1000px)'),rows={},lit=null,up=false,lastY=scrollY,cur=-2,raf=0,was;
if(list)[].forEach.call(list.querySelectorAll('a[href^="#"]'),function(a){rows[a.hash]=a;});
function laid(){return getComputedStyle(panel).position!=='fixed';}
function shown(){return laid()?root.getAttribute('data-toc')!=='closed':root.hasAttribute('data-tocpanel');}
function sync(){btn.setAttribute('aria-expanded',shown());}
function keep(v){try{v==='open'?localStorage.removeItem(K):localStorage.setItem(K,v);}catch(e){}}
function open(){
  if(laid()){root.setAttribute('data-toc','open');keep('open');}else root.setAttribute('data-tocpanel','');
  sync();redo();var a=links[cur]||links[0];
  panel.scrollTop=a.offsetTop+mark.offsetParent.offsetTop-panel.clientHeight/3;
  a.focus({preventScroll:true});}
function shut(back){
  if(laid()){root.setAttribute('data-toc','closed');keep('closed');}else root.removeAttribute('data-tocpanel');
  sync();if(back)btn.focus({preventScroll:true});}
btn.onclick=function(){shown()?shut(true):open();};
page.querySelector('.tocpanel__x').onclick=page.querySelector('.tocscrim').onclick=function(){shut(true);};
addEventListener('keydown',function(e){if(e.key==='Escape'&&shown()&&(!laid()||panel.contains(document.activeElement))){
  e.preventDefault();shut(true);}});
panel.addEventListener('click',function(e){var a=e.target.closest('a');if(!a||laid())return;  /* chosen: close, jump */
  shut(false);var h=document.getElementById(a.hash.slice(1));
  if(h){h.tabIndex=-1;setTimeout(function(){h.focus({preventScroll:true});});}});
panel.addEventListener('focusout',function(e){var t=e.relatedTarget;
  if(!laid()&&shown()&&t&&t!==btn&&!panel.contains(t))shut(false);});
function tick(){
  raf=0;
  var dy=scrollY-lastY;if(Math.abs(dy)>8){up=dy<0;lastY=scrollY;}
  var r=list&&list.getBoundingClientRect(),
    below=!r||r.top>innerHeight,past=!!r&&r.bottom<0;   /* the card: not reached, or passed */
  btn.classList.toggle('is-on',below||past&&(up||!PH.matches));
  var line=innerHeight*.3,i=heads.length;
  if(innerHeight+scrollY<root.scrollHeight-4)
    while(i--&&!(heads[i]&&heads[i].getBoundingClientRect().top<line));
  else i--;                                       /* at the foot, the last section */
  if(i===cur)return;
  var old=panel.querySelectorAll('[aria-current],.is-open');
  for(var k=0;k<old.length;k++){old[k].removeAttribute('aria-current');old[k].classList.remove('is-open');}
  cur=i;if(i<0){mark.classList.remove('is-on');return;}   /* the card keeps the last one */
  var a=links[i],li=a.closest('.toc__list>li');a.setAttribute('aria-current','true');
  if(li){li.classList.add('is-open');var r=rows[li.firstElementChild.hash]||null;
    if(r!==lit){if(lit)lit.classList.remove('is-last');lit=r;if(lit)lit.classList.add('is-last');}}
  place();mark.classList.add('is-on');
  var t=a.offsetTop+mark.offsetParent.offsetTop;
  if(shown()&&(t<panel.scrollTop||t+a.offsetHeight>panel.scrollTop+panel.clientHeight))
    panel.scrollTop=t-panel.clientHeight/3;
}
function place(){var a=links[cur];                /* the mark on the row, wherever it now lies */
  if(a)mark.style.transform='translateY('+a.offsetTop+'px) scaleY('+a.offsetHeight+')';}
function redo(){cur=-2;tick();}
if(window.ResizeObserver)new ResizeObserver(place).observe(panel.querySelector('.toc__list'));
addEventListener('scroll',function(){if(!raf)raf=requestAnimationFrame(tick);},{passive:true});
function relaid(){var now=laid();                 /* the width, or the site's column, moved it */
  if(now!==was)root.removeAttribute('data-tocpanel');was=now;sync();redo();}
addEventListener('resize',relaid);
new MutationObserver(relaid).observe(root,{attributes:true,attributeFilter:['data-side']});
was=laid();sync();tick();
"""


def render(**_kw):
    """The document pages' markup is written by build.py; this part is CSS and JS."""
    return ""
