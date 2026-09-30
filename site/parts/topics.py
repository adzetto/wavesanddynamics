# -*- coding: utf-8 -*-
"""Explore the topics: the six topics on the home page, as an index.

Rows 5 to 10 of his column, in its order. Each row is a subject icon, his
row title and his sub-line, and at its end, where the row leads: the site's
arrow, or, for a page still in preparation, a quiet "In preparation" in its
place (and, to a screen reader, as the link's description). The whole row
is the link. A wide list sets the six as one index, the titles in one column
and the sub-lines in the next, so they read down like a table of contents;
narrower, each sub-line goes under its title, and on a phone "In
preparation" goes under it too. Nothing boxes a row: at rest it is a
hairline and the paper. Every selector is scoped under .topics and every
colour is a page token; no :root variable is written. The root keeps
id="topics".

render(items) takes the rows from build.py (topic_items(): href, title,
sub, icon, soon), each title and sub-line inserted as given. Without items
it draws the same six from DEFAULT_ITEMS.

The rows answer in the site's own language. Under a mouse the warm wash
fills the row from the left in 380ms, as it fills his linked words
(theme.py's .inlink) and the rows of the site's other lists; the icon warms
to the accent and the arrow steps 3px on. Leaving is quicker, 160ms, as
leaving always is on the site, so a pointer or a key running down the list
never trails a wake of folding rows behind it. A press gives the row a little
under the finger (scale .98). A key lands on the finished state at once,
inside a ring: a key is answered now. A page in preparation stays quiet: no
arrow, no warmth, only the plain fill a list row takes. Hover lives inside
(hover:hover) and (pointer:fine), so a finger never leaves a row lit.

The arrival is the section's one motion: the first time the list is
scrolled to, each row's hairline draws from the left and its words follow,
the rows 45ms apart. The script looks on scroll, once a frame at most, with
no IntersectionObserver (parts/masthead.py says why). It hides the rows only
once they are about to come into view, so a page nobody scrolls never hides
them, and it stops looking once they have arrived. The rows are
.topics__row, not the .topics__item that theme.py's reveal selects: that
reveal holds its targets in an IntersectionObserver, and on the home page it
was the one observer left.
"""

__all__ = ["CSS", "JS", "render", "DEFAULT_ITEMS", "ICONS"]

CSS = """
/* ---------- explore the topics ---------- */

/* The list is the query container, not the section: containment on the
   section would stop the h2's top margin collapsing and push the heading off
   the page rhythm. Its four columns are the wide index's (icon, title,
   sub-line, the row's end); narrower, each row spans them all and lays
   itself out. */
.topics{--topics-bleed:12px}
.topics__list{container:topics/inline-size;list-style:none;margin:0;padding:0;
  max-width:var(--measure-fig);display:grid;
  grid-template-columns:28px minmax(0,5fr) minmax(0,7fr) max-content;column-gap:24px}

/* A row, narrow: the icon beside the title's first line, the sub-line under
   the title, the arrow at the row's end, centred on it. The row gives a
   little under a press (.98), back in 160ms. */
.topics__row{grid-column:1/-1;position:relative;isolation:isolate;margin:0;
  display:grid;grid-template-columns:28px minmax(0,1fr) auto;
  grid-template-areas:"icon title end" "icon desc end" "icon soon end";
  column-gap:16px;align-items:start;padding:18px 0 19px;
  transition:transform var(--spring-fast)}
/* the hairline is a border, so forced-colors mode keeps it */
.topics__row::before{content:"";position:absolute;top:0;left:0;right:0;
  border-top:1px solid var(--rule);transform-origin:0 0;
  transition:opacity var(--t-quick) var(--ease-state)}
/* The warm wash, laid ready and folded to the row's left edge: on hover it
   unfolds across the row, bled 12px past the words so none touches its
   edge. It hangs from the hairline, square under it, round at its foot.
   The transitions written on the resting state are the leaving ones, the
   shorter token; the lit state writes its own, longer, for arriving. */
.topics__row::after{content:"";position:absolute;z-index:-1;
  inset:0 calc(-1 * var(--topics-bleed));border-radius:0 0 var(--r-sm) var(--r-sm);
  background:var(--wash);transform:scaleX(0);transform-origin:0 50%;
  transition:transform var(--spring-fast)}
/* a page in preparation takes the plain fill of a list row instead, faded
   in rather than swept: warm means action, and this row has none yet */
.topics__row--soon::after{background:color-mix(in oklab,var(--ink) 4%,var(--page));
  transform:none;opacity:0;transition:opacity var(--t-quick) var(--ease-state)}

/* the subject icon: ink with one detail in the accent, warming whole to the
   accent on hover */
.topics__icon{grid-area:icon;display:block;width:28px;height:28px;color:var(--ink);
  overflow:visible;transition:color var(--t-fast) var(--ease-state)}
.topics .i-accent{stroke:var(--accent)}
.topics__title{grid-area:title;margin:0;font:600 21px/1.3 var(--serif);
  letter-spacing:-.004em;color:var(--ink);text-wrap:balance}
/* the whole row is the link's hit area, and the focus ring is drawn on it */
.topics__link{color:inherit;text-decoration:none;-webkit-tap-highlight-color:transparent}
.topics__link::after{content:"";position:absolute;inset:0 calc(-1 * var(--topics-bleed));
  border-radius:var(--r-sm)}
/* his sub-line: the serif at 17px in the body colour (7.72:1; 7.00:1 on the
   wash). A line of subjects, not prose, so it stays a step under the 19px
   reading size. On a phone it runs to three lines, where balancing broke
   "non-neural" at its hyphen, so it is only balanced from 560px, where it
   takes two at most. */
.topics__desc{grid-area:desc;margin:4px 0 0;font:400 17px/1.5 var(--serif);
  color:var(--body);text-wrap:pretty}
/* a page still in preparation: one quiet line in the interface's voice, the
   sans in capitals at 12px, --muted (5.10:1, 4.62:1 on a fill), as every
   "In preparation" on the site is set */
.topics__soon{grid-area:soon;margin:8px 0 0;font:600 12px/1.2 var(--sans);
  letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
/* the site's arrow (build.py's ARROW), whole: --muted at rest, the accent
   under the pointer, 3px on. forced-color-adjust:auto hands it the link's
   system colour under forced colours, where the svg's own would stay */
.topics__go{grid-area:end;align-self:center;display:block;width:24px;height:24px;
  color:var(--muted);forced-color-adjust:auto;
  transition:color var(--t-fast) var(--ease-state),transform var(--spring-fast)}

/* From 560px "In preparation" stands at the row's end, where a live row
   has its arrow. */
@container topics (min-width:560px){
  .topics__row{column-gap:20px}
  .topics__desc{text-wrap:balance}
  .topics__soon{grid-area:end;align-self:center;margin:0}
}
/* From 840px the six are one index: every row takes the list's four columns
   (a subgrid), so the titles share one column and the sub-lines the next,
   title and sub-line on one baseline, the ends in one column at the right. */
@container topics (min-width:840px){
  .topics__row{grid-template-columns:subgrid;grid-template-areas:none;
    align-items:baseline;padding:20px 0 21px}
  .topics__icon{grid-area:1/1;align-self:start}
  .topics__title{grid-area:1/2}
  .topics__desc{grid-area:1/3;margin:0}
  .topics__go,.topics__soon{grid-area:1/4;align-self:center;justify-self:end}
}

/* The states. Hover, for a pointer that can hover: the wash unfolds from
   the left, the icon and the arrow warm, the arrow steps 3px on. The lit
   row's fill ends on its own rounded foot: the next row's hairline fades
   while it is lit, as in the Gallery's rows. */
@media (hover:hover) and (pointer:fine){
  .topics__row:hover::after{transform:none;transition-duration:380ms}
  .topics__row--soon:hover::after{opacity:1;transition-duration:var(--t-quick)}
  .topics__row:not(.topics__row--soon):hover .topics__icon{color:var(--accent);
    transition-duration:200ms}
  .topics__row:hover .topics__go{color:var(--accent);transform:translateX(3px);
    transition-duration:200ms,380ms}
  .topics__row:hover+.topics__row::before{opacity:0}
}
/* A press, for everyone: the row gives a little, and the fill is there at
   once for a finger, which has no hover to bring it; a row in preparation
   takes its fill one step deeper. */
.topics__row:active{transform:scale(.98)}
.topics__row:active::after{transform:none;transition-duration:var(--t-quick)}
.topics__row--soon:active::after{opacity:1;
  background-color:color-mix(in oklab,var(--ink) 7%,var(--page))}
.topics__row:active+.topics__row::before{opacity:0}
/* Keyboard focus: the ring round the whole row, 2px in --focus, and the lit
   state with it, all at once, with no travel. */
.topics__link:focus-visible{outline:0}
.topics__link:focus-visible::after{outline:2px solid var(--focus);outline-offset:2px}
.topics__row:has(.topics__link:focus-visible)::after{transform:none;transition:none}
.topics__row--soon:has(.topics__link:focus-visible)::after{opacity:1}
.topics__row:not(.topics__row--soon):has(.topics__link:focus-visible) .topics__icon{
  color:var(--accent);transition:none}
.topics__row:has(.topics__link:focus-visible) .topics__go{color:var(--accent);
  transform:translateX(3px);transition:none}
.topics__row:has(.topics__link:focus-visible)+.topics__row::before{opacity:0;transition:none}

/* The arrival. Motion is added here, never clawed back: the start state
   exists only on screen, only without a reduced-motion request, and only
   under .topics--armed, which the script adds as the list is about to come
   into view; until the rows are in, a stray pointer cannot light what it
   cannot see. Then .topics--in: each hairline draws left to right, the words
   follow 60ms behind it, the rows 45ms apart (--i, the row's place). The
   script takes both classes off once the last row is in, so the arrival's
   timings never linger on the hover's. */
@media screen and (prefers-reduced-motion:no-preference){
  .topics--armed .topics__row::before{transform:scaleX(0)}
  .topics--armed .topics__row>*{opacity:0;transform:translateY(8px)}
  .topics--armed:not(.topics--in) .topics__row{pointer-events:none}
  .topics--in .topics__row::before{transform:none;
    transition:transform var(--spring-slow) calc(var(--i,0) * 45ms)}
  .topics--in .topics__row>*{opacity:1;transform:none;
    transition:opacity var(--t-slow) var(--ease),transform var(--spring-slow);
    transition-delay:calc(var(--i,0) * 45ms + 60ms)}
}

/* The icons draw on hover (see _LIVE): the moving lines are a second copy,
   hidden and wound back (a dash as long as the line, pathLength 1), that
   draws itself over its base, dimmed to a trace, while the pointer is on
   the row or focus is on its link, and is gone again at once when it
   leaves. Each keeps its own timing: the wave runs out and comes back from
   the wall, the bars rise 50ms apart and the curve is laid over them, the
   cursor steps along as the line is typed. Under reduced motion the icons
   stay as they are. */
.topics .t-run{opacity:0}
@media (prefers-reduced-motion:no-preference){
  .topics .t-run{stroke-dasharray:1 2;stroke-dashoffset:1;
    transition:opacity 0s 200ms,stroke-dashoffset 0s 200ms}
  .topics .t-base{transition:opacity var(--t-fast) var(--ease-state)}
  .topics .t-win{transition:transform var(--spring-mid)}
  .topics .t-type{transition:stroke-dashoffset 150ms steps(3,start),opacity 0s 150ms}
  .topics .t-caret{transition:transform 150ms steps(3,start)}
}
@media (hover:hover) and (prefers-reduced-motion:no-preference){
  .topics__row:hover .t-base{opacity:.3}
  .topics__row:hover .t-run{opacity:1;stroke-dashoffset:0}
  .topics__row:hover .t-in{transition:opacity 0s 40ms,stroke-dashoffset 220ms linear 40ms}
  .topics__row:hover .t-out{transition:opacity 0s 260ms,stroke-dashoffset 110ms linear 260ms}
  .topics__row:hover .t-fit{transition:opacity 0s 40ms,
    stroke-dashoffset var(--t-draw) var(--ease-in-out) 40ms}
  .topics__row:hover .t-win{transform:translateX(7px);
    transition:transform var(--t-draw) var(--ease-in-out)}
  .topics__row:hover .t-bar{transition:opacity 0s var(--d),
    stroke-dashoffset var(--spring-fast) var(--d)}
  .topics__row:hover .t-bell{transition:opacity 0s 140ms,
    stroke-dashoffset var(--t-mid) var(--ease-in-out) 140ms}
  .topics__row:hover .t-type{transition:opacity 0s,stroke-dashoffset 300ms steps(3,start)}
  .topics__row:hover .t-caret{transform:translateX(5.2px);
    transition:transform 300ms steps(3,start)}
}
.topics__row:has(.topics__link:focus-visible) .t-base{opacity:.3;transition:none}
.topics__row:has(.topics__link:focus-visible) .t-run{opacity:1;stroke-dashoffset:0;transition:none}
.topics__row:has(.topics__link:focus-visible) .t-win{transform:translateX(7px);transition:none}
.topics__row:has(.topics__link:focus-visible) .t-caret{transform:translateX(5.2px);transition:none}
"""

JS = """
/* Explore the topics. iOS Safari shows :active only where a touch listener
   is registered, so the section gets an empty one: a tap then presses the
   row. The arrival stands down under reduced motion.
   The arrival: the rows are visible by default. The list is looked at on
   scroll and resize, once a frame at most, and when the fonts or the page
   finish loading or the column folds, since each can move it without a
   scroll. While it is still more than a quarter screen below the fold
   nothing happens; once it is within that quarter screen the rows are
   hidden (.topics--armed), unseen below the fold; once its top is a tenth
   of a screen into view they arrive (.topics--in). A list already on
   screen at the first look is left as it is. Once they are in, every
   listener goes, and the two classes go 900ms later, when the last row has
   landed. build.py wraps every part's script in its own function scope. */
var root=document.querySelector('.topics');
if(!root)return;
root.addEventListener('touchstart',function(){},{passive:true});
var list=root.querySelector('.topics__list');
if(!list||!matchMedia('screen and (prefers-reduced-motion: no-preference)').matches)return;
var look=0,armed=false,done=false,fold=null;
function check(){
  look=0;
  if(done)return;
  var top=list.getBoundingClientRect().top,h=innerHeight;
  if(!armed){
    if(top>1.25*h)return;
    if(top<h){stop();return;}
    armed=true;root.classList.add('topics--armed');
    return;
  }
  if(top<.9*h){
    stop();root.classList.add('topics--in');
    setTimeout(function(){root.classList.remove('topics--armed','topics--in');},900);
  }
}
function soon(){if(!look)look=requestAnimationFrame(check);}
function stop(){
  done=true;removeEventListener('scroll',soon);removeEventListener('resize',soon);
  removeEventListener('load',soon);if(fold)fold.disconnect();
}
addEventListener('scroll',soon,{passive:true});
addEventListener('resize',soon);
addEventListener('load',soon);
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(soon);
if(window.MutationObserver){
  fold=new MutationObserver(soon);
  fold.observe(document.documentElement,{attributes:true,attributeFilter:['data-side']});
}
soon();
"""

# DESIGN_BRIEF 7.1 and 7.3: 24-unit grid drawn at 28px, stroke-width 1.2 (a 1.4px
# visual stroke), ink on the paper, exactly one detail in --accent.
_SVG = ('<svg class="topics__icon" viewBox="0 0 24 24" width="28" height="28" '
        'fill="none" stroke="currentColor" stroke-width="1.2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
        'focusable="false">')

# Vibrations and Waves. A wave meeting a wall, and the wave that comes back
# from it (the accent).
_WAVES = (_SVG + '<path d="M2.6 9.2c1.2-3 2.4-3 3.6 0s2.4 3 3.6 0 2.4-3 3.6 0 2.4 3 3.6 0"/>'
          '<path d="M20.6 3.2v17.6"/>'
          '<path class="i-accent" d="M17 14.8c-1.2 3-2.4 3-3.6 0s-2.4-3-3.6 0"/></svg>')

# Signal Processing, System Identification. An analysis window over a measured
# trace; the window is the accent.
_WINDOW = _SVG + ('<path d="M2.6 12.4 4.6 8.2 6.4 14.6 8.4 6.4 10.4 15.8 12.4 7.2 '
                  '14.2 14.2 16.2 9.4 18 13.2 19.6 10.4 21.4 12"/>'
                  '<rect class="i-accent" x="7.4" y="3.6" width="6.2" '
                  'height="16.8" rx="1.4"/></svg>')

# Machine Learning. A decision boundary between two labelled classes, hollow
# and filled, on the axes of a plot; the boundary is the accent.
_BOUNDARY = (_SVG + '<path d="M3.2 3.4v17.4h17.4"/>'
             '<path class="i-accent" d="M6.4 18.2C9.6 16.4 10.4 11.2 13.4 8.8c2-1.6 4.2-2.6 6.6-3"/>'
             '<circle cx="7.4" cy="10.4" r="1.5"/>'
             '<circle cx="11" cy="5.4" r="1.5"/>'
             '<circle cx="14.6" cy="15.4" r="1.5" fill="currentColor" stroke="none"/>'
             '<circle cx="18.6" cy="11.8" r="1.5" fill="currentColor" stroke="none"/>'
             '</svg>')

# Probability, Statistics. A histogram of samples on its baseline and the
# distribution fitted over it; the fitted curve is the accent. Each bar stops
# about 1.4 units under the curve.
_STATS = (_SVG + '<path d="M2.6 20.4h18.8M8.2 20.4v-5.8M12 20.4v-12.2M15.8 20.4v-5"/>'
          '<path class="i-accent" d="M2.6 19.4C5.6 19.4 6.6 17.4 7.8 14.4 9 11.4 10 6.2 12 6.2 '
          '14 6.2 15 11.4 16.2 14.4 17.4 17.4 18.4 19.4 21.4 19.4"/></svg>')

# Python / Programming. Python's own prompt, twice, as a session reads: a line
# already run, and under it the prompt waiting with its cursor (the accent).
_PROMPT = ("M2.6 4.2l2.4 2.4-2.4 2.4M6.4 4.2l2.4 2.4-2.4 2.4M10.2 4.2l2.4 2.4-2.4 2.4"
           "M2.6 13.8l2.4 2.4-2.4 2.4M6.4 13.8l2.4 2.4-2.4 2.4M10.2 13.8l2.4 2.4-2.4 2.4")
_PYTHON = (_SVG + f'<path d="{_PROMPT}"/><path d="M15 6.6h6.4"/>'
           '<path class="i-accent" d="M15.2 12.6v7.2"/></svg>')

# Communication. A speech bubble carrying a result, a line rising across it;
# the line is the accent.
_BUBBLE = ("M5.2 4h13.6a2.6 2.6 0 0 1 2.6 2.6v7.6a2.6 2.6 0 0 1-2.6 2.6h-8.4"
           "l-4.2 3.6v-3.6H5.2a2.6 2.6 0 0 1-2.6-2.6V6.6A2.6 2.6 0 0 1 5.2 4z")
_COMM = (_SVG + f'<path d="{_BUBBLE}"/>'
         '<path class="i-accent" d="M6.6 12.8l3.4-3.4 2.8 2.2 4.6-4.4"/></svg>')

# The icon for each subject, by the names build.py's TOPIC_ICONS gives them.
ICONS = {
    "vibrations-waves": _WAVES,
    "signal-processing": _WINDOW,
    "machine-learning": _BOUNDARY,
    "probability-statistics": _STATS,
    "python-programming": _PYTHON,
    "communication": _COMM,
}


# The same six, as the rows draw them: each carries a second copy of the
# lines that move (t-run, pathLength 1), hidden until the row is hovered or
# focused, when it draws itself over its base (t-base), dimmed to a trace:
# the wave runs to the wall and back, the window slides along the trace, the
# boundary is fitted, the bars rise one after another and the distribution
# is laid over them, the waiting line is typed with its cursor stepping on,
# and the result climbs across the bubble. The icons ICONS holds stay still,
# for the pages that show them without a row to hover (the Big Picture).
_LIVE = {
    'vibrations-waves': '<svg class="topics__icon" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path class="t-base" d="M2.6 9.2c1.2-3 2.4-3 3.6 0s2.4 3 3.6 0 2.4-3 3.6 0 2.4 3 3.6 0"/><path class="t-run t-in" d="M2.6 9.2c1.2-3 2.4-3 3.6 0s2.4 3 3.6 0 2.4-3 3.6 0 2.4 3 3.6 0" pathLength="1"/><path d="M20.6 3.2v17.6"/><path class="i-accent t-base" d="M17 14.8c-1.2 3-2.4 3-3.6 0s-2.4-3-3.6 0"/><path class="i-accent t-run t-out" d="M17 14.8c-1.2 3-2.4 3-3.6 0s-2.4-3-3.6 0" pathLength="1"/></svg>',
    'signal-processing': '<svg class="topics__icon" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.6 12.4 4.6 8.2 6.4 14.6 8.4 6.4 10.4 15.8 12.4 7.2 14.2 14.2 16.2 9.4 18 13.2 19.6 10.4 21.4 12"/><rect class="i-accent t-win" x="7.4" y="3.6" width="6.2" height="16.8" rx="1.4"/></svg>',
    'machine-learning': '<svg class="topics__icon" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3.2 3.4v17.4h17.4"/><path class="i-accent t-base" d="M6.4 18.2C9.6 16.4 10.4 11.2 13.4 8.8c2-1.6 4.2-2.6 6.6-3"/><path class="i-accent t-run t-fit" d="M6.4 18.2C9.6 16.4 10.4 11.2 13.4 8.8c2-1.6 4.2-2.6 6.6-3" pathLength="1"/><circle cx="7.4" cy="10.4" r="1.5"/><circle cx="11" cy="5.4" r="1.5"/><circle cx="14.6" cy="15.4" r="1.5" fill="currentColor" stroke="none"/><circle cx="18.6" cy="11.8" r="1.5" fill="currentColor" stroke="none"/></svg>',
    'probability-statistics': '<svg class="topics__icon" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.6 20.4h18.8"/><path class="t-base" d="M8.2 20.4v-5.8"/><path class="t-run t-bar" d="M8.2 20.4v-5.8" pathLength="1" style="--d:0ms"/><path class="t-base" d="M12 20.4v-12.2"/><path class="t-run t-bar" d="M12 20.4v-12.2" pathLength="1" style="--d:50ms"/><path class="t-base" d="M15.8 20.4v-5"/><path class="t-run t-bar" d="M15.8 20.4v-5" pathLength="1" style="--d:100ms"/><path class="i-accent t-base" d="M2.6 19.4C5.6 19.4 6.6 17.4 7.8 14.4 9 11.4 10 6.2 12 6.2 14 6.2 15 11.4 16.2 14.4 17.4 17.4 18.4 19.4 21.4 19.4"/><path class="i-accent t-run t-bell" d="M2.6 19.4C5.6 19.4 6.6 17.4 7.8 14.4 9 11.4 10 6.2 12 6.2 14 6.2 15 11.4 16.2 14.4 17.4 17.4 18.4 19.4 21.4 19.4" pathLength="1"/></svg>',
    'python-programming': '<svg class="topics__icon" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.6 4.2l2.4 2.4-2.4 2.4M6.4 4.2l2.4 2.4-2.4 2.4M10.2 4.2l2.4 2.4-2.4 2.4M2.6 13.8l2.4 2.4-2.4 2.4M6.4 13.8l2.4 2.4-2.4 2.4M10.2 13.8l2.4 2.4-2.4 2.4"/><path d="M15 6.6h6.4"/><path class="t-run t-type" d="M14.8 16.2h3.4" pathLength="1"/><path class="i-accent t-caret" d="M15.2 12.6v7.2"/></svg>',
    'communication': '<svg class="topics__icon" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5.2 4h13.6a2.6 2.6 0 0 1 2.6 2.6v7.6a2.6 2.6 0 0 1-2.6 2.6h-8.4l-4.2 3.6v-3.6H5.2a2.6 2.6 0 0 1-2.6-2.6V6.6A2.6 2.6 0 0 1 5.2 4z"/><path class="i-accent t-base" d="M6.6 12.8l3.4-3.4 2.8 2.2 4.6-4.4"/><path class="i-accent t-run t-fit" d="M6.6 12.8l3.4-3.4 2.8 2.2 4.6-4.4" pathLength="1"/></svg>',
}

# The site's arrow (build.py's ARROW), one path: its shaft and its head.
_GO = ('<svg class="topics__go" viewBox="0 0 24 24" width="24" height="24" fill="none" '
       'stroke="currentColor" stroke-width="1.25" stroke-linecap="round" '
       'stroke-linejoin="round" aria-hidden="true" focusable="false">'
       '<path d="M3.5 12h13M11.5 6.8l5.2 5.2-5.2 5.2"/></svg>')

# An icon name build.py does not send is looked up by the words of its link.
_GUESS = (("wave", "vibrations-waves"), ("vibration", "vibrations-waves"),
          ("signal", "signal-processing"), ("machine", "machine-learning"),
          ("probab", "probability-statistics"), ("statist", "probability-statistics"),
          ("python", "python-programming"), ("program", "python-programming"),
          ("communic", "communication"))

# Rows 5 to 10 of his column (build.py's NAV and topic_items()): his titles,
# less the comma his slide runs on with, and his sub-lines.
DEFAULT_ITEMS = (
    {"href": "doc/dynamical-behavior-of-engineering-structures-and-acoustic-wave-"
             "propagation.html",
     "title": "Vibrations and Waves", "sub": "All vibrations are waves",
     "icon": "vibrations-waves", "soon": False},
    {"href": "doc/signal-processing-system-identification-and-optimization.html",
     "title": "Signal Processing, System Identification",
     "sub": "Estimation, Inverse Problems, Optimization, Machine Learning",
     "icon": "signal-processing", "soon": False},
    {"href": "doc/machine-learning-the-complete-picture-and-guide-5.html",
     "title": "Machine Learning",
     "sub": "Neural and non-neural methods, Data Science vs ML Engineer",
     "icon": "machine-learning", "soon": False},
    {"href": "probability-statistics.html", "title": "Probability, Statistics",
     "sub": "Stochastic Process, Estimation", "icon": "probability-statistics",
     "soon": True},
    {"href": "python-programming.html", "title": "Python / Programming", "sub": "",
     "icon": "python-programming", "soon": True},
    {"href": "communication.html", "title": "Communication",
     "sub": "Meetings, presentations, reports, papers", "icon": "communication",
     "soon": True},
)


def _icon(item):
    name = item.get("icon") or ""
    if name not in _LIVE:
        words = f'{item.get("href", "")} {item.get("title", "")}'.lower()
        name = next((n for key, n in _GUESS if key in words), "")
    return _LIVE.get(name, "")


def _row(n, item):
    """One row: the icon, the title as the link, his sub-line, and at the
    row's end the arrow, or the quiet line that says the page is still in
    preparation. --i is its place, for the arrival's cascade."""
    href, title = item["href"], item["title"]
    sub = (item.get("sub") or "").strip()
    soon = bool(item.get("soon"))
    tag = f"topics-soon-{n}"
    desc = f' aria-describedby="{tag}"' if soon else ""
    body = f'\n   <p class="topics__desc">{sub}</p>' if sub else ""
    end = f'<p class="topics__soon" id="{tag}">In preparation</p>' if soon else _GO
    cls = "topics__row topics__row--soon" if soon else "topics__row"
    return (f'  <li class="{cls}" style="--i:{n - 1}">\n   {_icon(item)}\n'
            f'   <h3 class="topics__title"><a class="topics__link" href="{href}"{desc}>'
            f'{title}</a></h3>{body}\n   {end}\n  </li>')


def render(items=None):
    """Return the 'Explore the topics' section as an HTML string.

    items: the rows in order, each a dict of href, title, sub (his sub-line,
    may be empty), icon (a key of ICONS) and soon (the page is in
    preparation). Titles and sub-lines are his words and go in as given.
    """
    items = list(DEFAULT_ITEMS if items is None else items)
    rows = "\n".join(_row(n, it) for n, it in enumerate(items, 1))
    return ('<section class="topics" id="topics" aria-labelledby="topics-h">\n'
            ' <h2 id="topics-h">Explore the topics</h2>\n'
            ' <ul class="topics__list" role="list">\n'
            + rows
            + '\n </ul>\n</section>')
