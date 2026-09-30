# -*- coding: utf-8 -*-
"""rboxes - the four documents on My Research Areas, and the page's layout.

His deck draws four boxes in a row, his label on top and an icon below. Here
each document is a card: a hairline, his label as an h3 whose link ends in
the site's arrow, and a foot with the Word original on the left and the
plate, his icon redrawn, on the right. The whole card opens the document
(the label link's ::after spans it); the Word line is a link of its own that
sits above that span, never nested inside it. On a wide page the four stand
one under another in a column beside his text, all four in the first screen
of a 1280x800 window; on a narrow page they follow his text, two across from
480px. page_research() in build.py writes the .rboxes-page markup that this
CSS lays out. Card vocabulary, arrow and stroke ladder: DESIGN_BRIEF.md
sections 4, 4.1 and 7.1.

Motion, each piece for a reason (Motion's springs from theme.py for
travel, the --t tokens for colour and opacity):
- Arrival, once: the hairlines draw left to right, then the labels, then the
  feet, then each plate's signal blooms out from its source, the cards 70ms
  apart, so the eye is led down the column in reading order. On screen at
  load it plays at once, in CSS; a card still below the fold waits there
  (the script) and arrives as it comes into view. Over in 900ms.
- Lit, under a pointer: the warm wash unfolds from the left, as it does on
  his linked words and on the site's other rows; the arrow's shaft draws
  and its head slides 5px; the plate acts: its wavefronts step out from
  their source, the inner first, or the record is written again. The words
  in his text that the document takes further are marked in the same wash:
  that is the column's relation to the text beside it. A press gives a
  little (.98).
- A key lands on the finished state at once, with no travel, in a ring.
- Reduced motion: no arrival and no act; the wash fades in and the arrow
  stands whole.
"""
import html

__all__ = ["CSS", "JS", "render"]

CSS = """
/* ---------- rboxes: the four documents on My Research Areas ---------- */
/* The size container is a wrapper round the list, not the section: a size
   container is its own formatting context, so on .rboxes it would keep the
   h2's 47px top margin inside and add it to the paragraph's 22px above,
   leaving 69px over the heading against 47px over every other h2. */
.rboxes__body{container:rboxes/inline-size}
.rboxes__grid{display:grid;grid-template-columns:minmax(0,1fr);gap:12px 32px;
  margin:0;padding:0;list-style:none}

/* A card. The hairline and the text keep the column's left edge; the wash
   and the link's reach bleed 12px past them, so a lit fill never touches a
   letter. The foot sits at the bottom, so cards side by side put their
   plates on one line. */
.rboxes__doc{position:relative;isolation:isolate;display:grid;
  grid-template-rows:1fr auto;row-gap:4px;min-width:0;margin:0;padding:16px 0 12px;
  transition:transform var(--spring-fast)}
/* the hairline is a border, so forced colours keep it */
.rboxes__doc::before{content:"";position:absolute;top:0;left:0;right:0;
  border-top:1px solid var(--rule);transform-origin:0 0}
/* The warm wash, laid ready and folded to the card's left edge. It hangs
   from the hairline, square under it, round at its foot. The transition
   written here is the leaving one; the lit state writes its own, longer. */
.rboxes__doc::after{content:"";position:absolute;z-index:-1;inset:0 -12px;
  border-radius:0 0 var(--r-md) var(--r-md);background:var(--wash);
  transform:scaleX(0);transform-origin:0 50%;transition:transform var(--spring-fast)}

.rboxes__title{align-self:start;margin:0;font:600 19px/1.35 var(--serif);
  color:var(--ink);text-wrap:balance;overflow-wrap:break-word}
.rboxes__link{color:inherit;text-decoration:none;-webkit-tap-highlight-color:transparent}
/* the whole card is the link's target, and its focus ring is drawn here */
.rboxes__link::after{content:"";position:absolute;inset:0 -12px;border-radius:var(--r-md)}
/* The site's arrow after the label's last word, held to it by a no-break
   space, where the eye finishes reading the label. It draws at 1:1 (24
   units in 24px), so its 5-unit slide is 5px; its centre line sits on the
   middle of the x-height, and its negative margins keep the line box and
   the label's measure as they are. It is furniture, as in the Gallery:
   --muted at rest, one step toward the ink when lit. forced-color-adjust:
   auto hands it the link's system colour under forced colours, where the
   svg's own colour would stay. */
.rboxes__arrow{display:inline-block;width:24px;height:24px;margin:-8px -6px -8px -3px;
  vertical-align:middle;overflow:visible;color:var(--muted);forced-color-adjust:auto;
  transition:color var(--t-quick) var(--ease-state)}

/* The foot: the Word line on the left, the plate on the right. The line's
   baseline sits on the plate's ground line (y 19.6 of 24, 10.3px over the
   plate's foot), so the words and the drawing stand on one line; the plate
   is pulled 6px right so its ground line ends on the column's edge. */
.rboxes__foot{display:flex;align-items:flex-end;justify-content:space-between;
  gap:16px;min-width:0}
.rboxes__plate{flex:none;display:block;width:56px;height:56px;margin-right:-6px}
.rboxes .rb-w,.rboxes .rb-s{stroke:var(--accent)}
.rboxes .rb-m{opacity:.65}
.rboxes .rb-o{opacity:.35}
.rboxes .rb-run{opacity:0}
/* each plate's wavefronts are drawn round one source, and they move round it */
.rboxes .rb-span{--rb-src:12px 10px}
.rboxes .rb-slab{--rb-src:7px 10.6px}
.rboxes .rb-bearing{--rb-src:14.6px 10.2px}
.rboxes .rb-w>*{transform-origin:var(--rb-src,50% 50%)}

/* the Word line: a body link, format and size stated. Its 44px box keeps
   the target; its text is what sits on the ground line. */
.rboxes__dl{display:inline-flex;align-items:center;gap:8px;min-height:44px;
  margin:0 0 -7px;font:600 14px/1.3 var(--sans);letter-spacing:.01em;color:var(--muted)}
.rboxes__dl svg{flex:none;display:block;width:20px;height:20px;margin-left:-5px}
a.rboxes__dl{position:relative;z-index:1;color:var(--link);text-decoration:none;
  border-radius:var(--r-sm);-webkit-tap-highlight-color:transparent}
.rboxes__dlt{text-decoration-line:underline;text-decoration-thickness:1.5px;
  text-underline-offset:3px;text-decoration-color:currentColor;
  text-decoration-color:color-mix(in oklab,currentColor,transparent 62%);
  transition:text-decoration-color var(--t-fast) var(--ease-state)}
.rboxes__size{margin-left:2px;color:var(--muted);
  font-variant-numeric:lining-nums tabular-nums}
a.rboxes__dl:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
a.rboxes__dl:focus-visible .rboxes__dlt{text-decoration-color:currentColor}

/* not hosted yet: the same anatomy, no link, no arrow, no wash, the plate in
   --muted without its amber signal */
.rboxes__doc--wait .rboxes__plate{color:var(--muted)}
.rboxes__doc--wait :is(.rb-w,.rb-s){stroke:currentColor}

/* Two across from 480px of list. */
@container rboxes (min-width:480px){
  .rboxes__grid{grid-template-columns:repeat(2,minmax(0,1fr));row-gap:20px}
}

/* ---------- lit ---------- */
/* Under a pointer the wash unfolds from the left and the arrow steps one
   toward the ink; below, the arrow draws and the plate acts. The label
   takes no underline: beside the wash it was one signal too many. Over the
   Word line the card stands down (the :has() rules), since that line is a
   link of its own; a browser without :has() keeps the card lit there,
   which is harmless. */
@media (hover:hover) and (pointer:fine){
  .rboxes__doc:not(.rboxes__doc--wait):hover::after{transform:none;opacity:1;
    transition:transform var(--spring-draw),opacity var(--t-quick) var(--ease-state)}
  .rboxes__doc:hover .rboxes__arrow{color:var(--body)}
  a.rboxes__dl:hover .rboxes__dlt{text-decoration-color:currentColor}
  .rboxes__doc:has(.rboxes__dl:hover)::after{transform:scaleX(0);
    transition:transform var(--spring-fast)}
  .rboxes__doc:has(.rboxes__dl:hover) .rboxes__arrow{color:var(--muted)}
}
/* A key: the ring round the whole card, and the lit state at once. */
.rboxes__link:focus-visible{outline:0}
.rboxes__link:focus-visible::after{outline:2px solid var(--focus);outline-offset:2px}
.rboxes__doc:has(.rboxes__link:focus-visible)::after{transform:none;opacity:1;transition:none}
.rboxes__doc:has(.rboxes__link:focus-visible) .rboxes__arrow{color:var(--body);transition:none}
/* A press, for everyone: the wash at once, which a finger has no hover to
   bring, and the card gives a little under it */
.rboxes__doc:not(.rboxes__doc--wait):active::after{transform:none;opacity:1;
  transition-duration:var(--t-quick)}
.rboxes__doc:has(.rboxes__dl:active)::after{transform:scaleX(0)}
@media (prefers-reduced-motion:no-preference){
  .rboxes__doc:not(.rboxes__doc--wait):active{transform:scale(.98)}
  .rboxes__doc:has(.rboxes__dl:active){transform:none}
}

/* The arrow. At rest the shaft stops at the open end of the head. Lit, the
   shaft draws on left to right over 240ms and the head slides 5px, 60ms
   behind it, so the arrow grows by the same 5px it travels; letting go is
   quicker and unstaggered. A key gets the end state at once, as the hero's
   link does (round-4 finding RM-7). Travel is added only when no reduced
   motion is asked for, so everyone else gets the finished arrow, standing
   still. gallery.py and build.py's .row draw it with the same numbers. */
@media (prefers-reduced-motion:no-preference){
  .rboxes .ar-shaft{stroke-dasharray:13;stroke-dashoffset:5;
    transition:stroke-dashoffset var(--spring-fast)}
  .rboxes .ar-head{transition:transform var(--spring-fast)}
  .rboxes__doc:has(.rboxes__link:focus-visible) .ar-shaft{stroke-dashoffset:0;transition:none}
  .rboxes__doc:has(.rboxes__link:focus-visible) .ar-head{transform:translateX(5px);
    transition:none}
}
@media (hover:hover) and (pointer:fine) and (prefers-reduced-motion:no-preference){
  .rboxes__doc:hover .ar-shaft{stroke-dashoffset:0;transition-duration:var(--t-mid)}
  .rboxes__doc:hover .ar-head{transform:translateX(5px);
    transition:transform var(--spring-mid) 60ms}
  .rboxes__doc:has(.rboxes__dl:hover) .ar-shaft{stroke-dashoffset:5;
    transition:stroke-dashoffset var(--spring-fast)}
  .rboxes__doc:has(.rboxes__dl:hover) .ar-head{transform:none;
    transition:transform var(--spring-fast)}
}

/* The plate acts. Its wavefronts step out 15% from their source and
   strengthen, the inner first and the outer 100ms behind, as a front
   travels; letting go they settle back together. The record is written
   again: a second copy of its trace draws over the first, dimmed to a
   trace, and is gone at once when the card goes dark. */
@media (prefers-reduced-motion:no-preference){
  .rboxes .rb-w>*{transition:transform var(--spring-fast),opacity var(--t-fast) var(--ease-state)}
  .rboxes .rb-run{stroke-dasharray:1 2;stroke-dashoffset:1;
    transition:opacity 0s var(--t-quick),stroke-dashoffset 0s var(--t-quick)}
  .rboxes .rb-tr{transition:opacity var(--t-fast) var(--ease-state)}
  .rboxes__doc:has(.rboxes__link:focus-visible) .rb-w>*{transform:scale(1.15);opacity:1;
    transition:none}
  .rboxes__doc:has(.rboxes__link:focus-visible) .rb-w>.rb-m{opacity:.85}
  .rboxes__doc:has(.rboxes__link:focus-visible) .rb-w>.rb-o{opacity:.6}
  .rboxes__doc:has(.rboxes__link:focus-visible) .rb-w>.rb-tr{transform:none;opacity:.3}
  .rboxes__doc:has(.rboxes__link:focus-visible) .rb-w>.rb-run{transform:none;
    stroke-dashoffset:0}
}
@media (hover:hover) and (pointer:fine) and (prefers-reduced-motion:no-preference){
  .rboxes__doc:not(.rboxes__doc--wait):hover .rb-w>*{transform:scale(1.15);opacity:1;
    transition:transform var(--spring-mid),opacity var(--t-mid) var(--ease-state)}
  .rboxes__doc:not(.rboxes__doc--wait):hover .rb-w>.rb-m{opacity:.85;transition-delay:50ms}
  .rboxes__doc:not(.rboxes__doc--wait):hover .rb-w>.rb-o{opacity:.6;transition-delay:100ms}
  .rboxes__doc:not(.rboxes__doc--wait):hover .rb-w>.rb-tr{transform:none;opacity:.3}
  .rboxes__doc:not(.rboxes__doc--wait):hover .rb-w>.rb-run{transform:none;
    stroke-dashoffset:0;transition:opacity 0s,stroke-dashoffset var(--t-draw) var(--ease-in-out)}
  .rboxes__doc:has(.rboxes__dl:hover) .rb-w>*{transform:none;opacity:1;
    transition:transform var(--spring-fast),opacity var(--t-fast) var(--ease-state)}
  .rboxes__doc:has(.rboxes__dl:hover) .rb-w>.rb-m{opacity:.65}
  .rboxes__doc:has(.rboxes__dl:hover) .rb-w>.rb-o{opacity:.35}
  .rboxes__doc:has(.rboxes__dl:hover) .rb-w>.rb-run{opacity:0;stroke-dashoffset:1;
    transition:opacity 0s var(--t-quick),stroke-dashoffset 0s var(--t-quick)}
}
/* asked for less motion, the wash fades in where it would have unfolded */
@media (prefers-reduced-motion:reduce){
  .rboxes__doc::after{transform:none;opacity:0;
    transition:opacity var(--t-quick) var(--ease-state)}
  .rboxes__doc:has(.rboxes__dl:active)::after{transform:none;opacity:0}
}
@media (prefers-reduced-motion:reduce) and (hover:hover) and (pointer:fine){
  .rboxes__doc:has(.rboxes__dl:hover)::after{transform:none;opacity:0}
}

/* Forced colours paint no wash, so there the lit label is underlined
   instead (a colour cannot hide a line there, so it is drawn only when lit) */
@media (forced-colors:active){
  .rboxes__doc:has(.rboxes__link:focus-visible) .rboxes__t{text-decoration:underline 1px;
    text-underline-offset:4px}
}
@media (forced-colors:active) and (hover:hover) and (pointer:fine){
  .rboxes__doc:hover .rboxes__link .rboxes__t{text-decoration:underline 1px;
    text-underline-offset:4px}
  .rboxes__doc:has(.rboxes__dl:hover) .rboxes__link .rboxes__t{text-decoration:none}
}

/* The relation: while a document is lit, the words in his text that it
   takes further are marked in the same wash (the script names them; his
   text itself is never touched). */
.rboxes-page ::highlight(rboxes-ref){background-color:var(--wash);color:var(--ink)}

/* ---------- the arrival ---------- */
/* Once, in reading order: each hairline draws left to right, the label
   rises 8px into place 60ms behind it, the foot 60ms after that, and then
   the plate's signal blooms out from its source, inside first. The cards
   follow each other 70ms apart (--i, the card's place), so the last is in
   by 900ms. On screen at load it plays straight away, from the first frame,
   so nothing is shown and then taken back; a card still below the fold is
   held (.is-out, set by the script) and plays as it comes into view
   (.is-in, --d its delay among the cards arriving with it). The start state
   exists only on screen and only when no reduced motion is asked for, so
   print, reduced motion and a page without animations see the cards
   standing. */
@media screen and (prefers-reduced-motion:no-preference){
  .rboxes__doc{--rb-t:calc(var(--i,0) * 70ms)}
  .rboxes__doc.is-in{--rb-t:var(--d,0ms)}
  .rboxes__doc::before{animation:rboxes-draw var(--spring-slow) backwards;
    animation-delay:var(--rb-t)}
  .rboxes__title,.rboxes__foot{animation:rboxes-fade var(--t-slow) var(--ease) backwards,
    rboxes-rise var(--spring-slow) backwards;animation-delay:calc(var(--rb-t) + 60ms)}
  .rboxes__foot{animation-delay:calc(var(--rb-t) + 120ms)}
  .rboxes .rb-w>*{animation:rboxes-fade var(--t-mid) var(--ease) backwards,
    rboxes-bloom var(--spring-mid) backwards;animation-delay:calc(var(--rb-t) + 260ms)}
  .rboxes .rb-w>.rb-m{animation-delay:calc(var(--rb-t) + 310ms)}
  .rboxes .rb-w>.rb-o{animation-delay:calc(var(--rb-t) + 360ms)}
  .rboxes .rb-w>.rb-tr{animation:rboxes-write var(--t-draw) var(--ease-in-out) backwards;
    animation-delay:calc(var(--rb-t) + 260ms)}
  .rboxes .rb-w>.rb-run{animation:none}
  .rboxes__doc.is-out::before,.rboxes__doc.is-out .rboxes__title,
  .rboxes__doc.is-out .rboxes__foot,.rboxes__doc.is-out .rb-w>*{animation:none}
  .rboxes__doc.is-out::before{transform:scaleX(0)}
  .rboxes__doc.is-out .rboxes__title,.rboxes__doc.is-out .rboxes__foot{opacity:0}
}
@keyframes rboxes-draw{from{transform:scaleX(0)}}
@keyframes rboxes-fade{from{opacity:0}}
@keyframes rboxes-rise{from{transform:translateY(8px)}}
@keyframes rboxes-bloom{from{transform:scale(.6)}}
@keyframes rboxes-write{from{stroke-dasharray:1 2;stroke-dashoffset:1}
  to{stroke-dasharray:1 2;stroke-dashoffset:0}}

/* ---------- the page: his text, and the documents beside it ---------- */
/* page_research() sets his text, this list and the section after it ("The
   educational sections (topics in the big picture menu)", his heading and
   the paragraph he moved under it) in .rboxes-page__grid. Below 720px of
   page width the three run one after another. From 720px his text keeps
   the left and the documents stand one under another on the right, beside
   his text and the section under it, where his text has put them since his
   markup of 27 Sep 2026 ("The three documents on the right"): 720px gives
   his text 400px (about 46 characters) next to a 280px column, so a 1100px
   window (749px of page) sets them there too, and the page's full 924px
   gives it 604px, 4px short of the measure. 280px is the narrowest column
   that sets the first label in two lines (its longer line is 272px wide).
   The size container is a wrapper, not the grid, so the grid can change
   with it; as a container it keeps its children's margins in, so the last
   paragraph hands its margin back and the footer's 96px stays the gap
   above it. */
.rboxes-page{container:rboxes-page/inline-size}
.rboxes-page__more>p:last-child{margin-bottom:0}
/* the last card's 12px foot already leaves air under its ground line, so
   the heading after the documents takes 35px of its 47px */
.rboxes+.rboxes-page__more>h2{margin-top:35px}

@container rboxes-page (min-width:720px){
  .rboxes-page__grid{display:grid;
    grid-template-columns:minmax(0,var(--measure)) minmax(280px,1fr);
    grid-template-rows:auto 1fr;column-gap:40px;align-items:start}
  .rboxes-page__grid>.col--his{grid-area:1/1}
  .rboxes-page__more{grid-area:2/1}
  /* the column spans both rows, and the second is 1fr: a column taller than
     his text grows that row, never the first, so no gap opens under his
     text */
  .rboxes-page__grid>.rboxes{grid-area:1/2/3}
  /* a grid item keeps its margins: his text ends flush, and the heading
     under it takes the 47px every h2 has */
  .rboxes-page__grid>.col--his>p:last-child{margin-bottom:0}
  .rboxes+.rboxes-page__more>h2{margin-top:47px}

  /* The heading becomes the column's label, set as the About page sets its
     "Research areas". Its cap line is level with the cap line of his first
     line, which sits that line's half-leading ((--lh - 1.371)/2 of 19px,
     1.371 being Source Serif 4's ascent plus descent) and the font's ascent
     over its cap height (1.036 - .670) below the line's top; less the
     label's own cap offset in its 1.1 line (.202em of Source Sans 3). 6.7px
     at --lh 1.6, 6.2px at 1.55; measured level to a quarter pixel at 1100
     (column folded), 1152, 1280 and 1920. */
  .rboxes>h2{margin:calc(19px*((var(--lh) - 1.371)/2 + .366) - .202em) 0 14px;
    font:600 12px/1.1 var(--sans);letter-spacing:.12em;text-transform:uppercase;
    color:var(--muted)}
}
"""

JS = r"""
/* My Research Areas' documents; both jobs are enhancements. A document lit
   by a pointer or reached by a key marks the words in his text that it
   takes further, in a CSS highlight, so his text is never touched; a
   pointer passing over takes 80ms to mark, so a sweep down the column does
   not flicker his text. And a card still below the fold when the page
   opens waits there and arrives as it comes into view: the cards are seen
   by default, one is hidden only while it is off screen, a key that lands
   on one shows it at once, and the page is looked at on scroll and resize,
   once a frame at most (no IntersectionObserver: parts/masthead.py says
   why), and no longer once every card has arrived. iOS Safari shows
   :active only where a touch listener is registered. build.py wraps every
   part's script in its own function scope. */
var root=document.querySelector('.rboxes');
if(!root)return;
root.addEventListener('touchstart',function(){},{passive:true});
var docs=[].slice.call(root.querySelectorAll('.rboxes__doc'));
var his=document.querySelector('.rboxes-page .col--his'),reg=window.CSS&&CSS.highlights,tm=0;
function find(p){
  var w=document.createTreeWalker(his,4),s='',at=[],n,i,c;
  while((n=w.nextNode()))for(i=0;i<n.data.length;i++){c=n.data.charAt(i);
    if(/\s/.test(c)){if(s.slice(-1)===' ')continue;c=' ';}s+=c;at.push([n,i]);}
  i=p?s.indexOf(p):-1;if(i<0)return null;
  var r=document.createRange(),e=at[i+p.length-1];
  r.setStart(at[i][0],at[i][1]);r.setEnd(e[0],e[1]+1);return r;}
function mark(d,wait){clearTimeout(tm);reg.delete('rboxes-ref');
  if(d)tm=setTimeout(function(){var r=find(d.getAttribute('data-ref'));
    if(r)reg.set('rboxes-ref',new Highlight(r));},wait);}
if(his&&reg&&window.Highlight)docs.forEach(function(d){
  var a=d.querySelector('.rboxes__link');if(!a)return;
  a.addEventListener('pointerenter',function(e){if(e.pointerType!=='touch')mark(d,80);});
  a.addEventListener('pointerleave',function(){mark();});
  a.addEventListener('focus',function(){if(a.matches(':focus-visible'))mark(d,0);});
  a.addEventListener('blur',function(){mark();});});
if(his&&reg)addEventListener('pagehide',function(){mark();});
if(!matchMedia('screen and (prefers-reduced-motion: no-preference)').matches)return;
var wait=docs.filter(function(d){return d.getBoundingClientRect().top>innerHeight;}),f=0,ro;
if(!wait.length)return;
wait.forEach(function(d){d.classList.add('is-out');});
function look(){f=0;var k=0;
  wait=wait.filter(function(d){if(d.getBoundingClientRect().top>innerHeight*.92)return true;
    d.style.setProperty('--d',70*k++ +'ms');d.classList.replace('is-out','is-in');return false;});
  if(!wait.length){removeEventListener('scroll',soon);removeEventListener('resize',soon);
    if(ro)ro.disconnect();}}
function soon(){if(!f)f=requestAnimationFrame(look);}
addEventListener('scroll',soon,{passive:true});addEventListener('resize',soon);
if(window.ResizeObserver){ro=new ResizeObserver(soon);ro.observe(root);}
root.addEventListener('focusin',function(e){var d=e.target.closest('.rboxes__doc');
  if(d&&wait.indexOf(d)>=0){wait.splice(wait.indexOf(d),1);d.classList.remove('is-out');}});
"""

# Plates, 56px. The brief's stroke ladder puts them at stroke-width .75, a
# 1.75px line, so they read as drawings beside 1.25px inline icons. One family,
# one grid: every plate stands on the ground line y=19.6, every device and
# sheet is a rounded rect, and the one amber detail is what the instruments
# pick up: wavefronts stepping out 2.4 units round their source at opacity
# 1/.65/.35 (.rb-w, the part that moves), or on the record, the measured
# trace. Each plate redraws the subject of his own icon for that box on
# slide 3.
_PLATE = ('<svg class="rboxes__plate {0}" viewBox="0 0 24 24" width="56" height="56" '
          'fill="none" stroke="currentColor" stroke-width=".75" '
          'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">')

_ICONS = {
    # A span under watch: deck on two piers, a sensor at midspan, its field
    # rising off the structure (round the sensor's top, 12 10).
    "span": _PLATE.format("rb-span") + (
        '<path d="M2.6 19.6h18.8M7.8 15v4.6M16.2 15v4.6"/>'
        '<rect x="3.2" y="12.4" width="17.6" height="2.6" rx="1"/>'
        '<rect x="10.7" y="9.8" width="2.6" height="2.6" rx=".8"/>'
        '<g class="rb-w"><path d="M10 8.6a2.4 2.4 0 0 1 4 0"/>'
        '<path class="rb-m" d="M8.1 7.2a4.8 4.8 0 0 1 7.8 0"/>'
        '<path class="rb-o" d="M6.1 5.9a7.2 7.2 0 0 1 11.8 0"/></g></svg>'),
    # Inside the material: a probe on the surface, wavefronts spreading down
    # into the slab from where it touches (7 10.6), a crack growing up from
    # the back wall ahead of them.
    "slab": _PLATE.format("rb-slab") + (
        '<path d="M2.6 10.6h18.8M2.6 19.6h18.8"/>'
        '<rect x="4.7" y="8.2" width="4.6" height="2.4" rx=".8"/>'
        '<path d="M16.8 19.6 16.1 17.7l1.1-1.1-.6-1.4-.8-.8"/>'
        '<g class="rb-w"><path d="M9.2 11.6a2.4 2.4 0 0 1-2 1.4"/>'
        '<path class="rb-m" d="M11.3 12.6a4.8 4.8 0 0 1-3.9 2.8"/>'
        '<path class="rb-o" d="M13.5 13.6a7.2 7.2 0 0 1-5.9 4.2"/></g></svg>'),
    # A bearing on a source: the field spreads from a source out in the air
    # (14.6 10.2) down to the sensor on the ground that is holding its
    # direction.
    "bearing": _PLATE.format("rb-bearing") + (
        '<path d="M2.6 19.6h18.8"/>'
        '<rect x="3.3" y="17" width="2.6" height="2.6" rx=".8"/>'
        '<circle class="rb-s" cx="14.6" cy="10.2" r="1"/>'
        '<g class="rb-w"><path d="M13.3 13.6a3.6 3.6 0 0 1-2.3-2.8"/>'
        '<path class="rb-m" d="M12.5 15.8a6 6 0 0 1-3.8-4.7"/>'
        '<path class="rb-o" d="M11.6 18a8.4 8.4 0 0 1-5.3-6.5"/></g></svg>'),
    # The record of his two degrees: two sheets, the front one carrying a
    # measured response ringing down, drawn twice so it can be written again.
    # His deck marks this box with a report page and its figure, not a
    # screen on an easel.
    "record": _PLATE.format("rb-record") + (
        '<path d="M6.6 4.8v-.6A1.2 1.2 0 0 1 7.8 3h9.6a1.2 1.2 0 0 1 1.2 1.2'
        'v12.4a1.2 1.2 0 0 1-1.2 1.2h-.8"/>'
        '<rect x="3.4" y="4.8" width="12" height="14.8" rx="1.2"/>'
        '<path d="M5.8 7.6h5M5.8 17.2h7.2"/>'
        '<g class="rb-w">' + "".join(
            '<path class="{0}" pathLength="1" d="M5.8 12.6c.8 0 1-3.2 1.8-3.2s1 5.4 1.8 '
            '5.4 1-3.4 1.8-3.4 1 1.2 1.8 1.2"/>'.format(c) for c in ("rb-tr", "rb-run")) +
        '</g></svg>'),
}

# Brief 4.1, geometry as given: the shaft ends at x=16.5, which is where the
# open end of the head lands once it has slid 5 units. Drawn at 24px, not the
# snippet's 18px: at 18px a 5-unit slide is 3.75px on screen (measured), under
# the 5px the brief asks for. Stroke 1.25 keeps the ladder's 1.25px line.
_ARROW = ('<svg class="rboxes__arrow" viewBox="0 0 24 24" width="24" height="24" '
          'fill="none" stroke="currentColor" stroke-width="1.25" '
          'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
          '<path class="ar-shaft" d="M3.5 12h13"/>'
          '<path class="ar-head" d="m11.5 6.8 5.2 5.2-5.2 5.2"/></svg>')

# Download mark, inline class: 20px at stroke-width 1.5 (1.25px on screen).
_DL = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" '
       'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
       'stroke-linejoin="round" aria-hidden="true">'
       '<path d="M12 5v10m-4.5-4.5L12 15l4.5-4.5M6 19h12"/></svg>')

# Titles are his box labels from the deck (slide 3), as build.py transcribes
# them. Each box opens doc/<slug>.html. The Word files are his originals,
# unmodified, hosted as doc/<slug>.docx; "word" is his own file name, which
# the download attribute gives back to the saved copy. "mb" is the label used
# when render() is given no sizes: decimal MB of 113,742, 954,816 and 270,731
# bytes. "ref" is what the card marks in his text on My Research Areas while
# it is lit: the words there that the document takes further, as he wrote
# them (PROF_RESEARCH in build.py).
_DOCS = (
    {"slug": "brochure-shm-and-ndt-2-pages",
     "title": "Structural Health Monitoring / Non-destructive Testing (Short)",
     "icon": "span",
     "word": "Brochure - SHM and NDT - 2 pages.docx", "mb": "0.11",
     "ref": "Structural Health Monitoring (SHM) and Non-Destructive Testing (NDT)"},
    {"slug": "understanding-shm-and-ndt",
     "title": "Extended Structural Health Monitoring / Non-destructive Testing "
              "document",
     "icon": "slab",
     "word": "Understanding_SHM_and_NDT.docx", "mb": "0.95",
     "ref": "Structural Health Monitoring (SHM) and Non-Destructive Testing (NDT)"},
    {"slug": "sound-detection-and-tracking",
     "title": "Sound Wave Tracking",
     "icon": "bearing",
     "word": "Sound Detection and Tracking.docx", "mb": "0.27",
     "ref": "sound source tracking"},
    # The presentation opens as slides in presentation.html (parts/deck.py).
    {"slug": None, "href": "presentation.html",
     "title": "Extensive ppt regarding my MSc and PhD Research",
     "icon": "record",
     "word": None, "mb": None,
     "wait": "177 slides, in the browser",
     "ref": "presentation that walks through my master's and PhD work in more depth"},
)


def _title(text):
    """His label, kept whole: the slash stays with the word before it and
    Non-destructive never breaks at its hyphen. A word joiner (U+2060) after
    the hyphen does that; a nowrap span did too, but Chrome stops balancing a
    heading that holds one, and two labels ended on a lone word."""
    t = html.escape(text, quote=False).replace(" / ", "&nbsp;/ ")
    return t.replace("Non-destructive", "Non-⁠destructive")


def _mb(doc, sizes):
    """The size label in decimal MB, as the document pages print it: measured
    when build.py hands over the hosted file's bytes, typed otherwise."""
    n = (sizes or {}).get(doc["slug"])
    return doc["mb"] if n is None else "{0:.2f}".format(n / 1e6)


def _item(i, doc, docs_ready, sizes, hrefs=None):
    href = "doc/{0}.html".format(doc["slug"]) if doc["slug"] else doc.get("href")
    label = '<span class="rboxes__t">{0}</span>'.format(_title(doc["title"]))
    if href:
        # the arrow is held to the last word by a no-break space
        label = '<a class="rboxes__link" href="{0}">{1}&nbsp;{2}</a>'.format(
            href, label, _ARROW)
    if docs_ready and doc["word"]:
        # The name starts with the visible label (WCAG 2.5.3) and says which
        # of the three Word files this is.
        mb = _mb(doc, sizes)
        line = ('<a class="rboxes__dl" href="{4}" download="{0}" '
                'aria-label="Download Word, {1} MB: {2}">{3}'
                '<span class="rboxes__dlt">Download Word</span> '
                '<span class="rboxes__size">{1}&nbsp;MB</span></a>').format(
                    html.escape(doc["word"]), mb, html.escape(doc["title"]), _DL,
                    (hrefs or {}).get(doc["slug"], "doc/{0}.docx".format(doc["slug"])))
    else:
        line = '<p class="rboxes__dl">{0}<span>{1}</span></p>'.format(
            "" if doc.get("href") else _DL, doc.get("wait") or "Word file, coming soon")
    return ('  <li class="rboxes__doc{0}" style="--i:{1}"{2}>'
            '<h3 class="rboxes__title">{3}</h3>'
            '<div class="rboxes__foot">{4}{5}</div></li>').format(
                "" if href else " rboxes__doc--wait", i,
                ' data-ref="{0}"'.format(html.escape(doc["ref"])) if href and doc.get("ref") else "",
                label, line, _ICONS[doc["icon"]])


def render(docs_ready=False, sizes=None, hrefs=None):
    """Return the four research-document cards as an HTML string.

    docs_ready -- True once the three Word originals are hosted; the lines
    under the first three cards then become download links. The
    presentation opens in the browser either way.
    sizes -- optional {slug: bytes} of those hosted files. Each download line
    then states its file's measured size; a slug it leaves out keeps the
    size typed in _DOCS.
    hrefs -- optional {slug: url} of those files where they are hosted
    elsewhere; a slug it leaves out downloads doc/<slug>.docx.
    """
    items = "\n".join(_item(i, doc, docs_ready, sizes, hrefs) for i, doc in enumerate(_DOCS))
    # Not "Documents": that is the column row's old name, which the user
    # asked to retire (round-4 findings C3 and F8). His slide has no heading
    # here, but the page outline needs one between the h1 and the box
    # labels, and beside his text it labels the column.
    return ('<section class="rboxes" aria-labelledby="rboxes-h">\n'
            ' <h2 id="rboxes-h">Research documents</h2>\n'
            ' <div class="rboxes__body">\n'
            ' <ul class="rboxes__grid" role="list">\n' + items +
            '\n </ul>\n </div>\n</section>')
