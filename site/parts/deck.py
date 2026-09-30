"""His slide decks, a presenter for each: presentation.html and
probability-statistics.html.

The decks. His MSc and PhD presentation (PhD_MsC_entire_Review_ppt.pptx, 177
slides, exported from PowerPoint at 1600x900 into content/deck-phd/; the old
UT Austin address on slides 1 and 56 was replaced by
korkutkaynardag@iyte.edu.tr before export) and his Probability, statistics
and estimation (Prob__stat__stoch__est.pptx, 73 slides, 74 since the Kalman loop slide joined as 66 on 29 Sep 2026, exported through
PowerPoint's COM interface at 1920x1080 into content/deck-probstat/, with
each slide's title, its first text shape, in titles.json). The second deck's
text and speaker notes were read for addresses and phone numbers before it
went up; there are none, and the notes never ship. No .pptx is published.

The pictures. Each slide is written three times, into the deck's web/
folder: sNNN-1600.webp (quality 70), sNNN-960.webp (60) and sNNN-320.webp
(50), each brought down from the export with Lanczos (never up) and encoded
at WebP's slowest, smallest setting (method 6). At 1600 and 70 the thinnest
strokes, a hat over a mu or an index under an x, match the PowerPoint export
when laid side by side at twice the size; at 50 the orange of his captions
already ran. The page offers the 1600 and the 960 copy of every slide and
lets the browser choose by the stage's width (SIZES); the 320 copy is the
thumbnail (All slides, and the preview over a page number), the 960 copy
where a screen draws a tile with more pixels than that. build.py copies a
deck's folder to deck/<name>/ and hands render() its count.

The vectors (27 Sep 2026: "present diyince kalitesi düşüyor", presenting
lowered the quality). A 1600 picture enlarged to a large or Retina screen
goes soft. A deck whose folder also holds sNNN.svg, each slide printed as
vectors with his words as outlines (tools/deck/render.py), is drawn from
those wherever its picture would be enlarged: always while presenting, and
on the page where the stage has more device pixels than the 1600 copy (a
Retina laptop, a browser zoomed in, a pinch). The SVG is laid over the
picture, which shows first and stays under it, so nothing flashes; only the
slide on screen and its two neighbours fetch theirs.

The PDF ("slide'ı .pdf olarak indirilebilir olması lazım"). A deck with a
PDF of the whole (render(pdf=...)) offers it under its title the way the
site offers a Word file: the icon, "Download PDF" in the link's colour and
its size in decimal MB.

The page (the client's brief, 26 Sep 2026: a fine presenter, a Present
button, the pages as numbers; Apple's way of doing it). The slide is the
page: his title over it with the count, the one thing to do, Present, filled
in the warm accent beside it, and All slides beside that; under the slide a
capsule with a step either way and "12 / 73"; under that the pages as a row
of numbers, the one on screen filled, the row scrolling itself to keep it
in the middle and showing the slide a number stands for when the mouse
rests on it. Nothing else is on the page.

Moving through it. The arrows (either button, the left and right keys, Page
Up and Page Down, Home and End), a number, or a swipe. The keys are the
deck's while focus is in it or on nothing in particular, as when the page
has just opened; a link in the column keeps its own. A step cross-fades,
200ms, the slide coming up over the one it replaces, and a step taken while
one is fading starts from where things are (the old slide goes, the new one
fades). A swipe follows the finger: the slide moves with it, its neighbour
comes in from the side, and on release the pair finishes the move at the
speed the finger had, or springs back when the swipe was short and slow;
past the first or the last slide the stage gives a little and returns. The
next and the previous slide preload, so a step never waits for the
network. The address keeps the slide (#12), so a slide can be shared and
opened where it was, and the live region under the capsule tells a screen
reader which slide it is on. The numbers are one stop for the Tab key: on
them the arrows move the slide and the focus with it. A slide has no id of
its own: #12 is read by the script, so the browser never scrolls the page
down to a slide it has just shown.

Present (the button, P or F) gives the deck the whole screen through the
Fullscreen API, black round the slide as in a lecture hall, the capsule
floating over its foot in a dark glass; still for two and a half seconds,
the capsule and the pointer fade away and come back at the first move. A
click goes on, or back on the slide's left third, as a projector's clicker
would; Space goes on too. Escape, or the capsule's close button, ends it.
Where the browser has no Fullscreen API (an iPhone) the same view fills
the window instead.

All slides (the button, or G) opens every slide as a thumbnail with its
number and title in a modal <dialog>: focus lands on the slide on screen,
the arrow keys move through the grid, a click or Enter goes to a slide and
closes, Escape or G closes, and focus goes back to where it was. The
thumbnails load as they scroll into view.

Without JavaScript every slide is listed in order, lazily loaded, and the
buttons, the capsule and the numbers are not drawn. A printout gets every
slide. Under reduced motion nothing fades and the swipe changes slides
without following the finger; under reduced transparency the glass is
solid.
"""

import html

__all__ = ["CSS", "JS", "render", "SIZES"]

# The stage's width, for srcset: the page column's figure width (924px, the
# .wrap's 1020px less its padding) on a desktop, the window's width below the
# 1000px where the column folds away (a little over: the phone's stage runs
# to the edges, a tablet's keeps 22px each side).
SIZES = "(max-width: 1000px) 100vw, 924px"

# The PhD deck's page, as it has always read: the defaults of render().
PHD_SRC = "deck/phd/"
PHD_TITLE = "Extensive ppt regarding my MSc and PhD Research"

# The glyphs: the site's inline family (24-unit grid, stroke 1.5, drawn at 20px).
_SVG = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
        'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{0}</svg>')
_PREV = _SVG.format('<path d="M15 5l-7 7 7 7"/>')
_NEXT = _SVG.format('<path d="M9 5l7 7-7 7"/>')
# four slides on a table
_ALL = _SVG.format('<rect x="3.75" y="5.25" width="7" height="5.25" rx="1"/>'
                   '<rect x="13.25" y="5.25" width="7" height="5.25" rx="1"/>'
                   '<rect x="3.75" y="13.5" width="7" height="5.25" rx="1"/>'
                   '<rect x="13.25" y="13.5" width="7" height="5.25" rx="1"/>')
_CLOSE = _SVG.format('<path d="M6 6l12 12M18 6L6 18"/>')
# an arrow into a tray, the site's download glyph (the CV's and the Word links')
_DOWN = _SVG.format('<path d="M12 5v10m-4.5-4.5L12 15l4.5-4.5"/><path d="M6 19h12"/>')
# the play mark, filled, as on a presenter's remote
_PLAY = ('<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">'
         '<path fill="currentColor" d="M8 5.6v12.8a1 1 0 0 0 1.5.86l10.2-6.4a1 1 0 0 0 0-1.72L9.5 4.74A1 '
         '1 0 0 0 8 5.6z"/></svg>')

CSS = """
/* ---------- a deck's page: the title, what to do, the presenter ---------- */
.deck__top{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;
  gap:16px 24px;margin:0 0 24px}
.deck__top h1{margin:0}
.deck__meta{display:flex;flex-wrap:wrap;align-items:center;gap:0 22px;margin:8px 0 0;
  font:500 15px/1.4 var(--sans);color:var(--muted);font-variant-numeric:tabular-nums}
/* the deck as one PDF, offered as the site offers a Word file: the icon, the
   words in the link's colour, the size. Its 44px box keeps the target and
   reaches into the air round the line, which keeps its height. */
.deck__pdf{display:inline-flex;align-items:center;gap:8px;min-height:44px;margin:-11px 0;
  font-weight:600;color:var(--link);text-decoration:none;border-radius:var(--r-sm);
  -webkit-tap-highlight-color:transparent}
.deck__pdf svg{flex:none;width:20px;height:20px;margin-left:-2px}
.deck__pdft{text-decoration-line:underline;text-decoration-thickness:1.5px;text-underline-offset:3px;
  text-decoration-color:color-mix(in oklab,currentColor,transparent 62%);
  transition:text-decoration-color var(--t-fast) var(--ease-state)}
.deck__size{color:var(--muted);font-weight:500;font-variant-numeric:lining-nums tabular-nums}
@media (hover:hover){ .deck__pdf:hover .deck__pdft{text-decoration-color:currentColor} }
.deck__pdf:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.deck__pdf:focus-visible .deck__pdft{text-decoration-color:currentColor}
.deck__acts{display:none;gap:10px;flex-wrap:wrap}
.js .deck__acts{display:flex}
/* Present is the page's one call to act: filled, in the warm accent. All
   slides stands beside it in outline. Both answer the press, not the
   release. */
.deck__cta,.deck__ghost{display:inline-flex;align-items:center;justify-content:center;gap:8px;
  height:44px;margin:0;padding:0 20px 0 16px;border-radius:var(--r-pill);font:600 15px/1 var(--sans);
  letter-spacing:.005em;cursor:pointer;-webkit-tap-highlight-color:transparent;
  transition:background-color var(--t-fast) var(--ease-state),border-color var(--t-fast) var(--ease-state),
    transform var(--spring-quick)}
.deck__cta[hidden],.deck__ghost[hidden]{display:none}
.deck__cta{border:0;background:var(--accent);color:var(--btn-fg);
  box-shadow:0 1px 2px color-mix(in oklab,var(--accent) 35%,transparent)}
.deck__ghost{border:1px solid var(--line);background:var(--page);color:var(--ink)}
.deck__cta svg,.deck__ghost svg{width:18px;height:18px;flex:none}
@media (hover:hover){
  .deck__cta:hover{background:var(--accent-hover)}
  .deck__ghost:hover{background:var(--surface);border-color:var(--line-strong)}
}
.deck__cta:active{background:var(--accent-press);transform:scale(.97)}
.deck__ghost:active{transform:scale(.97)}
.deck__cta:focus-visible,.deck__ghost:focus-visible{outline:2px solid var(--focus);outline-offset:3px}

/* The stage. The deck is as wide as the window's height lets the slide, the
   capsule and the numbers be seen whole under the title: 330px is what
   stands over and under the slide (the title and its line, the capsule's
   64px with the air over it, the numbers' 52px and the air under them). */
.deck{position:relative;margin:0;max-width:max(480px,calc((100vh - 330px) * 16 / 9))}
.deck__stage{position:relative;background:#fff;border-radius:var(--r-lg);overflow:hidden;
  box-shadow:0 0 0 1px color-mix(in oklab,var(--ink) 9%,transparent),
    0 2px 4px color-mix(in oklab,var(--ink) 5%,transparent),
    0 22px 44px -22px color-mix(in oklab,var(--ink) 30%,transparent);
  touch-action:pan-y pinch-zoom;-webkit-user-select:none;user-select:none;
  -webkit-tap-highlight-color:transparent}
.deck__stage:focus{outline:none}
/* pinched in: the finger pans the enlarged page, and the swipe waits */
.deck__stage.is-zoomed{touch-action:auto}
.deck__list{position:relative;list-style:none;margin:0;padding:0}
/* build.py sets every li .35em from its neighbours; not a slide's */
.deck__list>li,.deck__grid>li,.deck__pages>li{margin:0}
.deck__list>li>img{display:block;width:100%;height:auto;-webkit-user-drag:none}
/* the slide as vectors, laid over its picture: the picture shows until the
   SVG has arrived and stays under it, so the swap is only a sharpening */
.deck__list>li>img.deck__vec{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
/* With a script, one slide. The shell marks <html> "js" in <head>, so the
   first paint already shows the first slide alone: the list of every slide
   never flashes up and collapses. */
.js .deck__list>li{display:none}
.js .deck:not(.is-live) .deck__list>li:first-child,
.deck.is-live .deck__list>li.on,.deck.is-live .deck__list>li.peek,.deck.is-live .deck__list>li.was{display:block}
.deck:not(.is-live) .deck__list>li+li{margin-top:16px}
/* a step: the new slide fades up over the one it replaces, which waits
   under it and goes when the fade is done */
.deck__list>li.on{position:relative;z-index:1}
.deck__list>li.was{position:absolute;top:0;left:0;width:100%;z-index:0}
.deck__list>li.in{animation:deck-in 200ms var(--ease) both}
@keyframes deck-in{from{opacity:0}}
/* a neighbour during a swipe, laid over the slide and moved beside it */
.deck__list>li.peek{position:absolute;top:0;left:0;width:100%;z-index:1}
.deck__list.is-dragging>li{will-change:transform}

/* The capsule under the slide: a step back, where you are, a step on. */
.deck__bar{display:none;width:max-content;margin:18px auto 0;padding:4px;align-items:center;gap:2px;
  border-radius:var(--r-pill);background:var(--surface);border:1px solid var(--rule);
  font:600 14px/1 var(--sans);color:var(--muted)}
.js .deck__bar{display:flex}
.deck__btn{display:grid;place-items:center;flex:none;width:40px;height:40px;margin:0;padding:0;
  border:0;border-radius:var(--r-pill);background:transparent;color:var(--ink);font:inherit;cursor:pointer;
  -webkit-tap-highlight-color:transparent;
  transition:background-color var(--t-fast) var(--ease-state),transform var(--spring-quick)}
.deck__btn[hidden]{display:none}
.deck__btn svg{width:20px;height:20px;pointer-events:none}
@media (hover:hover){
  .deck__btn:not([aria-disabled="true"]):hover{background:color-mix(in oklab,var(--ink) 7%,transparent)}
}
.deck__btn:not([aria-disabled="true"]):active{transform:scale(.92);
  background:color-mix(in oklab,var(--ink) 12%,transparent)}
.deck__btn:focus-visible{outline:2px solid var(--focus);outline-offset:1px}
/* the end of the deck: the button stays in the tab order, so focus is not
   lost from under the reader's finger, and says it has nowhere to go */
.deck__btn[aria-disabled="true"]{opacity:.32;cursor:default}
.deck__at{min-width:84px;padding:0 6px;text-align:center;font-variant-numeric:tabular-nums;white-space:nowrap}
.deck__cur{color:var(--ink)}
.deck__exit{display:none}
.deck__vh{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;
  clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap;border:0}

/* The pages as numbers: one row that scrolls under the slide, fading at
   its ends where there is more, the slide on screen filled in ink. */
.deck__nums{display:none;position:relative;margin:14px 0 0}
.js .deck__nums{display:block}
.deck__pages{display:flex;gap:4px;margin:0;padding:6px 28px;list-style:none;overflow-x:auto;
  overscroll-behavior-x:contain;scrollbar-width:none;
  -webkit-mask-image:linear-gradient(90deg,transparent,rgb(0 0 0) 28px,rgb(0 0 0) calc(100% - 28px),transparent);
  mask-image:linear-gradient(90deg,transparent,rgb(0 0 0) 28px,rgb(0 0 0) calc(100% - 28px),transparent)}
.deck__pages::-webkit-scrollbar{display:none}
.deck__pages>li{flex:none}
.deck__pg{display:grid;place-items:center;min-width:36px;height:34px;margin:0;padding:0 9px;border:0;
  background:transparent;cursor:pointer;
  border-radius:var(--r-pill);font:600 13.5px/1 var(--sans);font-variant-numeric:tabular-nums;
  color:var(--muted);text-decoration:none;-webkit-tap-highlight-color:transparent;
  transition:background-color var(--t-fast) var(--ease-state),color var(--t-fast) var(--ease-state)}
@media (hover:hover){ .deck__pg:hover{background:var(--surface);color:var(--ink)} }
.deck__pg:active{background:color-mix(in oklab,var(--ink) 10%,transparent)}
.deck__pg[aria-current="true"]{background:var(--ink);color:var(--page)}
.deck__pg:focus-visible{outline:2px solid var(--focus);outline-offset:1px}
/* what a number stands for, while the mouse rests on it */
.deck__tip{position:absolute;bottom:calc(100% + 4px);left:0;z-index:3;width:216px;padding:6px;
  border-radius:var(--r-md);background:var(--page);border:1px solid var(--line);
  box-shadow:0 14px 34px -10px color-mix(in oklab,var(--ink) 34%,transparent);pointer-events:none;
  opacity:0;transform:translate(-50%,6px) scale(.98);transform-origin:50% 100%;
  transition:opacity var(--t-fast) var(--ease),transform var(--spring-fast)}
.deck__tip.is-on{opacity:1;transform:translate(-50%,0)}
.deck__tip img{display:block;width:100%;height:auto;border-radius:4px;background:var(--card)}
.deck__tip span{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;
  margin:7px 3px 1px;font:500 12.5px/1.35 var(--sans);color:var(--body)}
.deck__tip b{margin-right:6px;color:var(--ink);font-variant-numeric:tabular-nums}

/* ---------- Present: the deck is the screen ---------- */
/* the page's scrollbar gutter (build.py keeps it stable) would stay beside
   the screen as a dark strip, the slide pushed off centre: it goes too */
html.deck-show{overflow:hidden;scrollbar-gutter:auto}
.deck.is-show{position:fixed;inset:0;z-index:90;max-width:none;margin:0;display:flex;align-items:center;
  justify-content:center;background:rgb(0 0 0)}
.deck.is-show::backdrop{background:rgb(0 0 0)}
.deck.is-show .deck__stage{width:min(100vw,calc(100vh * 16 / 9));border-radius:0;box-shadow:none;
  background:rgb(0 0 0)}
.deck.is-show .deck__nums{display:none}
/* the capsule floats over the slide's foot in a dark glass, and goes when
   the reader is still */
.deck.is-show .deck__bar{position:absolute;left:50%;bottom:max(24px,env(safe-area-inset-bottom));z-index:4;
  margin:0;transform:translateX(-50%);color:rgb(255 255 255 / .62);background:rgb(28 28 30 / .66);
  border-color:rgb(255 255 255 / .1);box-shadow:0 12px 30px rgb(0 0 0 / .3);
  -webkit-backdrop-filter:blur(22px) saturate(180%);backdrop-filter:blur(22px) saturate(180%);
  transition:opacity 280ms var(--ease),transform var(--spring-mid)}
.deck.is-show .deck__btn{color:rgb(255 255 255)}
@media (hover:hover){
  .deck.is-show .deck__btn:not([aria-disabled="true"]):hover{background:rgb(255 255 255 / .12)}
}
.deck.is-show .deck__btn:not([aria-disabled="true"]):active{background:rgb(255 255 255 / .2)}
.deck.is-show .deck__btn:focus-visible{outline-color:rgb(255 255 255)}
.deck.is-show .deck__cur{color:rgb(255 255 255)}
.deck.is-show .deck__exit{display:grid;margin-left:4px;box-shadow:-1px 0 0 rgb(255 255 255 / .12)}
.deck.is-show.is-idle{cursor:none}
.deck.is-show.is-idle .deck__bar:not(:focus-within){opacity:0;transform:translate(-50%,10px);pointer-events:none}
@media (prefers-reduced-transparency:reduce){
  .deck.is-show .deck__bar{background:rgb(28 28 30);-webkit-backdrop-filter:none;backdrop-filter:none}
}

/* ---------- All slides: the deck as a sheet of thumbnails ---------- */
.deck__all{position:fixed;inset:0;width:100%;height:100%;max-width:none;max-height:none;
  margin:0;padding:0;border:0;background:var(--page);color:var(--ink);overflow:auto;
  overscroll-behavior:contain;scroll-padding-top:88px;opacity:1;
  transition:opacity var(--t-fast) var(--ease)}
.deck__all::backdrop{background:transparent}
.deck__head{position:sticky;top:0;z-index:1;display:flex;align-items:center;
  justify-content:space-between;gap:16px;padding:14px 24px;
  background:color-mix(in oklab,var(--page) 86%,transparent);
  -webkit-backdrop-filter:blur(18px) saturate(160%);backdrop-filter:blur(18px) saturate(160%);
  border-bottom:1px solid var(--rule)}
.deck__h{margin:0;font:600 22px/1.25 var(--serif);letter-spacing:-.005em;color:var(--ink)}
.deck__head .deck__btn{border:1px solid var(--rule);width:44px;height:44px}
.deck__grid{list-style:none;max-width:1360px;margin:0 auto;padding:28px 24px 56px;display:grid;
  grid-template-columns:repeat(auto-fill,minmax(216px,1fr));gap:28px 20px;
  transition:transform var(--spring-mid)}
/* it opens as a sheet settling into place: a fade and 8px of rise */
@starting-style{
  .deck__all[open]{opacity:0}
  .deck__all[open] .deck__grid{transform:translateY(8px)}
}
.deck__tile{display:block;width:100%;margin:0;padding:0;border:0;background:none;color:inherit;
  font:inherit;text-align:left;cursor:pointer;-webkit-tap-highlight-color:transparent}
.deck__tile img{display:block;width:100%;height:auto;border-radius:var(--r-sm);background:var(--card);
  box-shadow:0 0 0 1px var(--line);
  transition:box-shadow var(--t-fast) var(--ease-state),transform var(--spring-quick)}
.deck__cap{display:flex;align-items:baseline;gap:10px;margin-top:10px;
  font:15px/1.35 var(--sans);color:var(--body)}
.deck__tn{flex:none;min-width:1.5em;font-size:13px;font-weight:600;color:var(--muted);
  font-variant-numeric:tabular-nums}
.deck__tt{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden}
/* the slide on screen, in the warm mark the column gives the current page */
.deck__tile[aria-current="true"] img{box-shadow:0 0 0 2px var(--accent)}
.deck__tile[aria-current="true"] .deck__tn{color:var(--accent)}
@media (hover:hover){
  .deck__tile:hover img{box-shadow:0 0 0 1px var(--line-strong)}
  .deck__tile[aria-current="true"]:hover img{box-shadow:0 0 0 2px var(--accent)}
  .deck__tile:hover .deck__tt{color:var(--ink)}
}
.deck__tile:active img{transform:scale(.98)}
.deck__tile:focus-visible{outline:none}
.deck__tile:focus-visible img{outline:2px solid var(--focus);outline-offset:3px}

/* A phone: the slide runs to the screen's edges (the .wrap's 22px each
   side), and the two buttons share the width under the title. */
@media (max-width:640px){
  .deck{max-width:none}
  .deck__stage{margin-inline:-22px;border-radius:0;
    box-shadow:0 0 0 1px color-mix(in oklab,var(--ink) 9%,transparent)}
  .deck__acts{width:100%}
  .deck__cta,.deck__ghost{flex:1}
  .deck__pages{margin-inline:-22px;padding-inline:22px}
  .deck__head{padding:10px 16px}
  .deck__h{font-size:20px}
  .deck__grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:20px 12px;padding:16px 16px 40px}
  .deck__cap{gap:8px;font-size:14px}
}
@media (pointer:coarse){ .deck__btn{width:44px;height:44px} .deck__pg{min-width:40px;height:40px} }

@media (forced-colors:active){
  .deck__bar,.deck__cta,.deck__ghost{border:1px solid ButtonBorder}
  .deck__pg[aria-current="true"]{outline:2px solid Highlight}
  .deck__tile[aria-current="true"] img{outline:2px solid Highlight;outline-offset:2px}
}
@media (prefers-reduced-motion:reduce){
  .deck__list>li.in{animation:none}
  .deck__btn,.deck__cta,.deck__ghost,.deck__pg,.deck__tip,.deck__all,.deck__grid,.deck__tile img,
  .deck.is-show .deck__bar{transition:none}
}
@media print{
  .deck__acts,.deck__bar,.deck__nums,.deck__all{display:none!important}
  .deck .deck__list>li{display:block!important;position:relative;break-inside:avoid}
  .deck .deck__list>li+li{margin-top:16px}
}
"""

JS = "var X='" + _CLOSE + "';" + r"""
var d=document.querySelector('.deck');if(!d)return;
var page=d.closest('.deckpage')||document,
    st=d.querySelector('.deck__stage'),list=d.querySelector('.deck__list'),
    li=[].slice.call(list.children),n=li.length,i=0;
if(!n)return;
var prev=d.querySelector('[data-go="-1"]'),next=d.querySelector('[data-go="1"]'),
    cur=d.querySelector('.deck__cur'),say=d.querySelector('.deck__say'),
    allb=page.querySelector('[data-all]'),showb=page.querySelector('[data-show]'),
    nums=d.querySelector('.deck__pages'),pgs=nums?[].slice.call(nums.querySelectorAll('.deck__pg')):[],
    root=document.documentElement,reduce=matchMedia('(prefers-reduced-motion: reduce)'),
    sizes=li[0].querySelector('img').getAttribute('sizes'),fading=0;
function pic(k){return li[k]&&li[k].querySelector('img')}
/* a slide's title is its alt text after "Slide N: "; a deck without titles
   says "Slide N of M", and its slides go by their numbers */
function titled(k){return pic(k).alt.replace(/^Slide \d+(?:: | of \d+$)/,'')}
function showing(){return d.classList.contains('is-show')}
/* presenting, a slide asks for the copy the screen needs, not the page's */
function fit(k){var im=pic(k),s=showing()?'100vw':sizes;if(im&&im.getAttribute('sizes')!==s)im.sizes=s}
function load(k){var im=pic(k);if(!im)return;fit(k);if(im.loading==='lazy')im.loading='eager'}
/* the vectors: wherever the picture would be enlarged (presenting, or a
   stage with more device pixels than the largest copy: a Retina screen, a
   zoom, a pinch), a slide is drawn from its SVG, laid over the picture. A
   deck with vectors publishes no 1600 copy, so its largest is the 960 */
var vec=d.hasAttribute('data-vector'),big=vec?960:1600;
function crisp(){var z=window.visualViewport;
  return showing()||st.clientWidth*(window.devicePixelRatio||1)*(z?z.scale:1)>big}
function sharp(k){
  var l=li[k];if(!vec||!l||l.querySelector('.deck__vec')||!crisp())return;
  var v=document.createElement('img');v.className='deck__vec';v.alt='';v.decoding='async';
  v.onerror=function(){v.remove()};
  v.src=pic(k).getAttribute('src').replace(/-\d+\.webp$/,'.svg');l.appendChild(v);
}
function sharpen(){sharp(i);sharp(i+1);sharp(i-1)}
/* the numbers: the one on screen filled, the only one Tab stops at, kept
   in the middle of the row without moving the page */
function number(k){
  if(!pgs.length)return;
  var o=nums.querySelector('[aria-current]');if(o){o.removeAttribute('aria-current');o.tabIndex=-1}
  var c=pgs[k];c.setAttribute('aria-current','true');c.tabIndex=0;
  nums.scrollLeft=c.offsetLeft-(nums.clientWidth-c.offsetWidth)/2;
  if(nums.contains(document.activeElement))c.focus({preventScroll:true});
}
function settle(){
  clearTimeout(fading);fading=0;
  for(var k=0;k<n;k++)li[k].classList.remove('was','in');
}
function show(k,push,tell,fade){
  k=Math.max(0,Math.min(n-1,k));
  settle();
  var was=li[i];
  was.classList.remove('on');i=k;li[i].classList.add('on');
  if(fade&&was!==li[i]&&!reduce.matches){
    was.classList.add('was');li[i].classList.add('in');fading=setTimeout(settle,240);
  }
  load(i);load(i+1);load(i-1);sharpen();
  prev.setAttribute('aria-disabled',i===0);next.setAttribute('aria-disabled',i===n-1);
  cur.textContent=i+1;number(i);
  if(push)try{history.replaceState(null,'','#'+(i+1))}catch(e){}
  if(tell)say.textContent='Slide '+(i+1)+' of '+n+(titled(i)?': '+titled(i):'');
}
function go(k){finish();k=Math.max(0,Math.min(n-1,k));if(k!==i)show(k,1,1,1)}
function hashed(){var m=/^#(\d+)$/.exec(location.hash);return m?m[1]-1:0}
d.classList.add('is-live');
show(hashed(),0,0);
addEventListener('hashchange',function(){finish();show(hashed(),0,1)});

d.addEventListener('click',function(e){
  var b=e.target.closest('[data-go]'),p=e.target.closest('.deck__pg');
  if(b&&b.getAttribute('aria-disabled')!=='true')go(i+ +b.getAttribute('data-go'));
  else if(p)go(+p.getAttribute('data-n')-1);
  else if(e.target.closest('[data-exit]'))leave();
});

/* The keys belong to the deck while focus is in it or on no control at all
   (the page as it loads): a link or a button elsewhere keeps its own keys,
   and so G, P and F, single letters, never fire from the column or a field
   (WCAG 2.1.4). No modifier may be held, and the phone's menu must be shut. */
function elsewhere(t){
  return t.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)||
    (!d.contains(t)&&!!t.closest('a[href],button,summary,[tabindex]'))}
document.addEventListener('keydown',function(e){
  if(e.defaultPrevented||e.altKey||e.ctrlKey||e.metaKey||root.classList.contains('nav-open'))return;
  if(box&&box.open){grid(e);return}
  if(showing())wake();
  if(elsewhere(e.target))return;
  var k=e.key;
  if(k==='ArrowRight'||k==='PageDown'||(k===' '&&showing()))go(i+1);
  else if(k==='ArrowLeft'||k==='PageUp')go(i-1);
  else if(k==='Home')go(0);
  else if(k==='End')go(n-1);
  else if((k==='g'||k==='G')&&allb&&!allb.hidden){if(!e.repeat)openAll()}
  else if(k==='p'||k==='P'||k==='f'||k==='F'){if(!e.repeat){if(showing())leave();else enter()}}
  else if(k==='Escape'&&showing())leave();
  else return;
  e.preventDefault();
});

/* ---- the swipe: the slide follows the finger ----
   Ten pixels decide the direction (a steeper move is the page's scroll and
   is left alone), and the slide then tracks from where the finger is, not
   from where it went down, so it does not jump. On release a quarter of
   the stage (at most 120px), or a flick past 24px, carries on to the
   neighbour; a twitch never turns a slide. The move takes as long
   as the finger's speed says (--ease leaves at four times its mean speed),
   within 160 to 300ms. */
var drag=null,settling=null,swallow=0,kind='';
function span(){return st.clientWidth+24}
function band(dx){var w=st.clientWidth;return dx*w*.55/(w+.55*Math.abs(dx))}
function edge(dx){return (dx>0&&i===0)||(dx<0&&i===n-1)?band(dx):dx}
function place(x,ms){
  for(var j=-1;j<=1;j++){var o=li[i+j];if(!o)continue;
    o.style.transition=ms?'transform '+ms+'ms cubic-bezier(.2,.8,.2,1)':'';
    o.style.transform='translateX('+(x+j*span())+'px)'}
}
function clear(){
  list.classList.remove('is-dragging');
  for(var j=-1;j<=1;j++){var o=li[i+j];if(o){o.classList.remove('peek');o.style.transition=o.style.transform=''}}
}
function finish(){
  if(!settling)return;
  var to=settling.to;clearTimeout(settling.t);settling=null;clear();
  if(to)show(i+to,1,1);
}
st.addEventListener('pointerdown',function(e){
  swallow=0;kind=e.pointerType;finish();
  if(drag||!e.isPrimary||e.button||e.target.closest('dialog')||st.classList.contains('is-zoomed'))return;
  settle();
  drag={id:e.pointerId,x:e.clientX,y:e.clientY,dx:0,v:0,lx:e.clientX,lt:e.timeStamp,on:0};
});
st.addEventListener('pointermove',function(e){
  var g=drag;if(!g||e.pointerId!==g.id)return;
  var dx=e.clientX-g.x,dy=e.clientY-g.y,dt=e.timeStamp-g.lt;
  if(!g.on){
    if(Math.abs(dy)>10&&Math.abs(dy)>Math.abs(dx)){drag=null;return}
    if(Math.abs(dx)<10)return;
    g.on=1;g.x+=dx>0?10:-10;dx=e.clientX-g.x;
    try{st.setPointerCapture(g.id)}catch(x){}
    if(!reduce.matches){
      list.classList.add('is-dragging');
      if(li[i-1])li[i-1].classList.add('peek');if(li[i+1])li[i+1].classList.add('peek');
    }
  }
  if(dt>0){g.v=.7*(e.clientX-g.lx)/dt+.3*g.v;g.lx=e.clientX;g.lt=e.timeStamp}
  g.dx=dx;
  if(!reduce.matches)place(edge(dx),0);
});
function up(e){
  var g=drag;if(!g||e.pointerId!==g.id)return;drag=null;
  if(!g.on)return;
  swallow=1;setTimeout(function(){swallow=0},0);
  var dir=g.dx<0?1:-1,
      far=Math.abs(g.dx)>Math.min(st.clientWidth/4,120)||
          (Math.abs(g.dx)>24&&Math.abs(g.v)>.35&&(g.v<0)===(dir>0)),
      to=e.type==='pointerup'&&far&&li[i+dir]?dir:0;
  if(reduce.matches){if(to)go(i+to);return}
  var from=edge(g.dx),end=-to*span(),
      ms=Math.round(Math.max(160,Math.min(300,4*Math.abs(end-from)/Math.max(Math.abs(g.v),.1))));
  place(end,ms);
  settling={to:to,t:setTimeout(finish,ms+40)};
}
st.addEventListener('pointerup',up);
st.addEventListener('pointercancel',up);
st.addEventListener('dragstart',function(e){e.preventDefault()});
/* a swipe's release is no click; presenting, a click with a mouse or a pen
   steps on, or back on the left third, as a projector's clicker would, and
   a tap brings the capsule back */
st.addEventListener('click',function(e){
  if(swallow){swallow=0;e.stopPropagation();return}
  if(!showing()||e.target.closest('dialog'))return;
  if(kind==='touch'){wake();return}
  var r=st.getBoundingClientRect();
  go(i+(e.clientX-r.left<r.width/3?-1:1));
},true);
var vv=window.visualViewport;
if(vv)vv.addEventListener('resize',function(){st.classList.toggle('is-zoomed',vv.scale>1.01);sharpen()});
addEventListener('resize',sharpen);

/* ---- Present ----
   The deck takes the screen through the Fullscreen API where there is one,
   and the window where there is not; either way the same view. Escape
   leaves full screen in the browser's own hands, and its change brings the
   page back. */
var fsOn=d.requestFullscreen||d.webkitRequestFullscreen,
    fsOff=document.exitFullscreen||document.webkitExitFullscreen,
    fsOk=!!(fsOn&&fsOff&&(document.fullscreenEnabled||document.webkitFullscreenEnabled)),
    idle=0;
function fsNow(){return (document.fullscreenElement||document.webkitFullscreenElement)===d}
function wake(){
  d.classList.remove('is-idle');clearTimeout(idle);
  idle=setTimeout(function(){if(showing())d.classList.add('is-idle')},2500);
}
function enter(){
  if(showing())return;
  if(box&&box.open)box.close();
  d.classList.add('is-show');root.classList.add('deck-show');
  fit(i);fit(i+1);fit(i-1);sharpen();wake();
  st.focus({preventScroll:true});
  say.textContent='Presenting, slide '+(i+1)+' of '+n;
  if(fsOk){var p=fsOn.call(d);if(p&&p.catch)p.catch(function(){})}
}
function done(){
  clearTimeout(idle);
  d.classList.remove('is-show','is-idle');root.classList.remove('deck-show');
  fit(i);fit(i+1);fit(i-1);
  if(showb)showb.focus({preventScroll:true});
}
function leave(){if(fsNow())fsOff.call(document);else if(showing())done()}
function changed(){if(!fsNow()&&showing())done()}
document.addEventListener('fullscreenchange',changed);
document.addEventListener('webkitfullscreenchange',changed);
d.addEventListener('pointermove',function(e){if(showing()&&e.pointerType!=='touch')wake()});
if(showb){showb.hidden=false;showb.addEventListener('click',enter)}

/* ---- what a number stands for ----
   With a mouse, resting on a number shows its slide's thumbnail and title
   over it, kept inside the row's width. */
if(nums&&matchMedia('(hover:hover) and (pointer:fine)').matches){
  var tip=document.createElement('div'),wrap=nums.parentNode;
  tip.className='deck__tip';tip.setAttribute('aria-hidden','true');
  tip.innerHTML='<img alt="" width="320" height="180" decoding="async"><span></span>';
  wrap.appendChild(tip);
  nums.addEventListener('pointerover',function(e){
    var a=e.target.closest('.deck__pg');if(!a||e.pointerType!=='mouse')return;
    var k=a.getAttribute('data-n')-1,t=titled(k);
    tip.firstChild.src=pic(k).getAttribute('src').replace(/-\d+\.webp$/,'-320.webp');
    tip.lastChild.innerHTML='<b>'+(k+1)+'</b>'+esc(t);
    var r=a.getBoundingClientRect(),w=wrap.getBoundingClientRect(),half=tip.offsetWidth/2;
    tip.style.left=Math.max(half,Math.min(w.width-half,r.left+r.width/2-w.left))+'px';
    tip.classList.add('is-on');
  });
  nums.addEventListener('pointerleave',function(){tip.classList.remove('is-on')});
  nums.addEventListener('scroll',function(){tip.classList.remove('is-on')},{passive:true});
}

/* ---- All slides ----
   Built on first use from the slides themselves: each slide's 320px copy,
   its number and its title. Where a tile has more pixels than that copy (a
   246px tile on a Retina screen is 492, a phone's 173px one at 3x is 519)
   the browser takes the 960px copy the viewer already publishes, so the
   overview is sharp and the site no heavier. The dialog sits inside the
   stage, so it shows while presenting too, and nothing in it reaches the
   swipe or the click above (both look for it). */
var box=null,tiles=[],back=null;
function esc(s){return s.replace(/[&<>"]/g,function(c){return '&#'+c.charCodeAt(0)+';'})}
function build(){
  var h='';
  for(var k=0;k<n;k++){var t=titled(k),u=esc(pic(k).getAttribute('src')).replace(/-\d+\.webp$/,'');
    h+='<li><button type="button" class="deck__tile" data-n="'+(k+1)+'"><img src="'+u+'-320.webp" srcset="'+
      u+'-320.webp 320w, '+u+'-960.webp 960w" sizes="(max-width: 640px) 45vw, 250px" '+
      'width="320" height="180" alt="" loading="lazy" decoding="async"><span class="deck__cap">'+
      '<span class="deck__tn"><span class="deck__vh">Slide </span>'+(k+1)+'</span>'+
      (t?'<span class="deck__tt">'+esc(t)+'</span>':'')+'</span></button></li>'}
  box=document.createElement('dialog');
  box.className='deck__all';box.setAttribute('aria-labelledby','deck-all-h');
  box.innerHTML='<div class="deck__head"><h2 class="deck__h" id="deck-all-h">All slides</h2>'+
    '<button type="button" class="deck__btn deck__x" aria-label="Close">'+X+'</button></div>'+
    '<ol class="deck__grid" role="list">'+h+'</ol>';
  st.appendChild(box);
  tiles=[].slice.call(box.querySelectorAll('.deck__tile'));
  box.addEventListener('click',function(e){
    var t=e.target.closest('.deck__tile');
    if(t){box.close();go(t.getAttribute('data-n')-1)}
    else if(e.target.closest('.deck__x'))box.close();
  });
  box.addEventListener('close',function(){
    var b=back;back=null;
    if(b&&b.isConnected&&b.focus)b.focus({preventScroll:true});
  });
}
function openAll(){
  if(!box)build();
  finish();
  back=document.activeElement;
  for(var k=0;k<n;k++){if(k===i)tiles[k].setAttribute('aria-current','true');else tiles[k].removeAttribute('aria-current')}
  box.showModal();
  var t=tiles[i];
  box.scrollTop=t.offsetTop-(box.clientHeight-t.offsetHeight)/2;
  t.focus({preventScroll:true});
}
/* in the grid: the arrows move by a tile or a row, Home and End to the ends */
function grid(e){
  var k=e.key;
  if(k==='g'||k==='G'){if(!e.repeat)box.close();e.preventDefault();return}
  var at=tiles.indexOf(document.activeElement);
  if(at<0)return;
  var c=1;while(c<n&&tiles[c].offsetTop===tiles[0].offsetTop)c++;
  var to=k==='ArrowRight'?at+1:k==='ArrowLeft'?at-1:k==='ArrowDown'?at+c:k==='ArrowUp'?at-c:
         k==='Home'?0:k==='End'?n-1:null;
  if(to===null)return;
  e.preventDefault();
  tiles[Math.max(0,Math.min(n-1,to))].focus();
}
if(window.HTMLDialogElement&&allb){allb.hidden=false;allb.addEventListener('click',openAll)}
addEventListener('beforeprint',function(){for(var k=0;k<n;k++)load(k)});
"""


def _alt(k, count, titles):
    """A slide's alt text: its number and its title, or its number of all."""
    t = " ".join(str(titles[k - 1]).split()) if titles and k <= len(titles) and titles[k - 1] else ""
    return f"Slide {k}: {t}" if t else f"Slide {k} of {count}"


def _mb(n):
    """A file's size as the site states one: decimal MB, two places."""
    return f"{n / 1e6:.2f}&nbsp;MB"


def render(count, up="", *, src=PHD_SRC, title=PHD_TITLE, lede=None, titles=None,
           vector=False, pdf=None):
    """A deck's page body: its <h1> and the line under it (by default the
    count), Present and All slides, the stage, the capsule, the numbers.

    `count` slides named sNNN-{320,960,1600}.webp under `up` + `src` (no
    1600 copy when `vector`);
    `title` is the <h1>; `lede` the line under it, as text; `titles` the
    slides' titles in order, which name each slide in its alt text, in All
    slides and over its number. `vector`: the folder also holds sNNN.svg,
    drawn wherever the pictures would be enlarged. `pdf`: (its address from
    the site's root, its size in bytes), offered under the title and saved
    under the deck's title. The defaults are the PhD deck's page."""
    base = html.escape(up + src)
    meta = html.escape(lede, quote=False) if lede is not None else f"{count} slides"
    if pdf:
        meta = (f'<span>{meta}</span><a class="deck__pdf" href="{html.escape(up + pdf[0])}" '
                f'download="{html.escape(title)}.pdf" type="application/pdf">{_DOWN}'
                f'<span class="deck__pdft">Download PDF</span> '
                f'<span class="deck__size">{_mb(pdf[1])}</span></a>')

    # a deck with vectors has no 1600 copy: past the 960 its SVG takes over
    big = "" if vector else ", {one}-1600.webp 1600w"

    def slide(k):
        one = f"{base}s{k:03d}"
        first = ' loading="eager" fetchpriority="high"' if k == 1 else ' loading="lazy"'
        return (f'<li><img src="{one}-960.webp" srcset="{one}-960.webp 960w{big.format(one=one)}" '
                f'sizes="{SIZES}" width="1600" height="900"{first} decoding="async" '
                f'alt="{html.escape(_alt(k, count, titles))}"></li>')

    items = "".join(slide(k) for k in range(1, count + 1))
    numbers = "".join(
        f'<li><button class="deck__pg" type="button" data-n="{k}" tabindex="-1" '
        f'aria-label="{html.escape(_alt(k, count, titles))}">{k}</button></li>'
        for k in range(1, count + 1))
    return f"""<div class="wrap deckpage">
 <div class="deck__top">
  <div><h1>{html.escape(title, quote=False)}</h1><p class="deck__meta">{meta}</p></div>
  <div class="deck__acts">
   <button class="deck__ghost" type="button" data-all aria-haspopup="dialog" aria-keyshortcuts="G" title="All slides (G)" hidden>{_ALL}<span>All slides</span></button>
   <button class="deck__cta" type="button" data-show aria-keyshortcuts="P" title="Present (P)" hidden>{_PLAY}<span>Present</span></button>
  </div>
 </div>
 <div class="deck"{' data-vector' if vector else ''}>
  <div class="deck__stage" tabindex="-1"><ol class="deck__list">{items}</ol></div>
  <div class="deck__bar">
   <button class="deck__btn" type="button" data-go="-1" aria-label="Previous slide">{_PREV}</button>
   <span class="deck__at"><span class="deck__cur">1</span> / {count}</span>
   <button class="deck__btn" type="button" data-go="1" aria-label="Next slide">{_NEXT}</button>
   <button class="deck__btn deck__exit" type="button" data-exit aria-label="End the presentation" title="End (Esc)">{_CLOSE}</button>
  </div>
  <nav class="deck__nums" aria-label="Slides"><ol class="deck__pages" role="list">{numbers}</ol></nav>
  <p class="deck__vh deck__say" aria-live="polite"></p>
 </div>
</div>"""
