# -*- coding: utf-8 -*-
"""Career: his route, with every stay drawn to its length.

Six roles, newest first, beside one line drawn like a route on a transit map.
The line keeps to one lane through his university years, steps out into a
second lane for the two posts in industry (Transtek, Renesas) and steps back
in for the professorship. Each role is a stop, and each stop is as long as he
stayed there: a 12px stop plus 8px a year, so the seven years at Austin read
at a glance and the year at Transtek is short. The present post is a filled
amber stop. The stretch that brought him back to a university is amber too,
and past it the line runs on and fades, because it is still being drawn. The
route begins at a terminus, in 2013.

The route is laid as the reader arrives, once, on the way down, by one pen
that runs from the present post back to the terminus in 2013 and never gets
ahead of the reader: a role is laid only once it has come into view. The
present stop opens with one amber ring, the line above it grows out of it,
and the pen leaves it amber. At each stop after that the pen dwells as long
as he stayed, 55ms a year, and the stop fills with light from its top while
it does: the seven years at Austin fill slowly, the year at Transtek in a
blink. Then the pen runs down the stretch to the next stop at an even pace,
the turn between the lanes included, while the light it left behind fades,
and the next stop opens on the site's spring as the line reaches it. So the
stretches of his career fill one after another, in their order, each for
its own length of time; the terminus bar settles in last. Only the route
moves: the words are never hidden. The route is hidden first only if the
reader scrolls while the section is still below the screen, so a page
nobody scrolls (a print, a preview, a screenshot) always shows it drawn.

Point at a role and the route answers. Its stop turns amber at once, a soft
fill opens from the stop across the row, and the role's own stretch draws in
amber from the stop below, filling the stop as it arrives. The rest of the
line steps back, the dates turn amber, and one faint ring leaves the stop.
Leaving is quicker than arriving. All of this needs a mouse or a trackpad:
on a touch screen the route stays at rest, so a tap never leaves a role lit.
Under reduced motion there is no entrance, every state still changes, in
place, and there is no ring.

The line is blue because blue means place on this site (DESIGN_BRIEF.md 1.4):
--link mixed into the paper, so it holds in both themes. It is drawn in
borders and SVG strokes, so it prints and follows forced colours.

Scoped under .career. The script only lays the route in (it times each role
from the route's own measured stretches); without it the route is simply
there. Nothing here is a link or a tab stop; every fact the
route draws is also in the text, and the route is hidden from assistive
technology. render() needs no arguments.
"""

__all__ = ["CSS", "JS", "render"]

# The rail in px: the centre of the outer (industry) lane, the step between
# the lanes, the rail's width. The CSS and the SVG turns both read these, so a
# turn always meets the straight runs.
PAD, LANE, RAIL = 7, 20, 34

CSS = """
/* ===================== Career: the route ===================== */
.career{container:career/inline-size}
/* Narrow first: the rail on the left, then dates, role, place and note.
   --career-dot is the centre of a stop's top below the item's top: the middle
   of the dates' line here, of the role's first line from 560px. A stop is
   --career-node wide and grows --career-year for every year of the role. */
.career__list{--career-pad:PADpx;--career-lane:LANEpx;--career-rail:RAILpx;
  --career-gap:28px;--career-dot:10.5px;--career-turn:40px;--career-node:12px;
  --career-year:8px;--career-foot:6px;
  --career-line:var(--line-strong);--career-lit:var(--surface);
  position:relative;isolation:isolate;max-width:var(--measure-wide);margin:0;
  padding:0;list-style:none}
/* The line: --link mixed 45% into the paper, #94B0CB, a soft blue at 2.14:1
   on the page (dark #394E63, 2.19:1). It is drawing, not information: every
   date it draws is in the text. The lit fill: --wash taken 38% back toward
   the paper, #FDF0E5; on it --body is 7.25:1 and --muted 4.79:1 (dark
   #261B15: 8.98 and 5.16). Both only where color-mix is understood.
   Elsewhere an unknown value would drop the stops' borders altogether, so
   the line falls back to --line-strong and the fill to --surface. */
@supports (color:color-mix(in oklab,red,blue)){
  .career__list{--career-line:color-mix(in oklab,var(--link) 45%,var(--page));
    --career-lit:color-mix(in oklab,var(--wash) 62%,var(--page))}
}
/* --x is the lane: 1 for a university, 0 for industry. --yrs is the stay in
   whole years, set on each item. Padding, not margin, spaces the roles, so a
   pointer moving down the list never falls between two of them. */
.career__item{--x:1;--yrs:0;--bend:0px;position:relative;display:grid;margin:0;
  padding:0 0 var(--career-gap);grid-template-columns:var(--career-rail) minmax(0,1fr);
  column-gap:12px;grid-template-areas:"rail when" "rail role" "rail place" "rail note";
  --career-top:calc(var(--career-dot) - var(--career-node) / 2);
  --career-len:calc(var(--career-node) + var(--yrs) * var(--career-year));
  --career-at:calc(var(--career-pad) + var(--x) * var(--career-lane))}
.career__item:last-child{padding-bottom:0}
.career__item--out{--x:0}
.career__item--turn{--bend:var(--career-turn)}

.career__role{grid-area:role;margin:0;font:600 21px/1.3 var(--serif);
  letter-spacing:-.004em;color:var(--ink);text-wrap:balance}
.career__when{grid-area:when;margin:0;white-space:nowrap;
  font:600 14px/1.5 var(--sans);letter-spacing:.01em;color:var(--muted);
  font-variant-numeric:lining-nums tabular-nums}
.career__item--now .career__when{color:var(--accent)}      /* 5.28:1 */
/* no font shorthand here: it would reset the body's old-style figures */
.career__place,.career__note{margin:4px 0 0;font-size:16px;line-height:1.5}
.career__place{grid-area:place;color:var(--body)}
.career__note{grid-area:note;color:var(--muted)}
/* a place breaks between its parts, never inside a name */
.career__part{display:inline-block;max-width:100%}

/* ---------- the route ----------
   Each role draws its own stretch: from the foot of its stop down to the top
   of the next one, in its own lane, turning into the next role's lane on the
   way if that role is in the other sector. The turn is an SVG S that leaves
   and arrives upright; the straight run is a border. The lit copy starts at
   the top of the stop and carries the stop's fill, all in --accent, clipped
   away from the top so that it draws upward, the way time runs on this list,
   and fills the stop last. */
.career__rail{grid-area:rail;position:relative}
.career__track{position:absolute;left:0;right:0;
  top:calc(var(--career-top) + var(--career-len));
  bottom:calc(-1 * (var(--career-gap) + var(--career-top)));color:var(--career-line)}
.career__item:last-child .career__track{bottom:var(--career-foot)}
.career__track::before{content:"";position:absolute;top:0;bottom:var(--bend);
  left:calc(var(--career-at) - 1px);border-left:2px solid currentColor}
.career__track svg{position:absolute;left:0;bottom:0;width:var(--career-rail);
  height:var(--career-turn);overflow:visible;fill:none;stroke:currentColor;
  stroke-width:2}
.career__track--lit{top:var(--career-top);color:var(--accent);
  clip-path:inset(100% 0 0 0)}
.career__item--now .career__track--lit{clip-path:inset(0)}
.career__fill{position:absolute;top:0;width:var(--career-node);
  height:var(--career-len);left:calc(var(--career-at) - var(--career-node) / 2);
  border-radius:var(--r-pill);background:currentColor}
/* the terminus: where the line starts, in 2013 */
.career__item:last-child .career__track::after{content:"";position:absolute;
  bottom:-1px;width:12px;border-top:2px solid currentColor;
  left:calc(var(--career-at) - 6px)}
/* past the present stop the line runs on and fades: it is still being drawn */
.career__item--now .career__rail::before{content:"";position:absolute;
  top:calc(var(--career-top) - 22px);height:24px;
  left:calc(var(--career-at) - 1px);border-left:2px solid var(--accent);
  -webkit-mask-image:linear-gradient(to top,#000,transparent);
  mask-image:linear-gradient(to top,#000,transparent)}

/* the stop: an outline as long as the stay; the present one is filled */
.career__node{position:absolute;z-index:1;box-sizing:border-box;
  top:var(--career-top);left:calc(var(--career-at) - var(--career-node) / 2);
  width:var(--career-node);height:var(--career-len);border-radius:var(--r-pill);
  border:2px solid var(--career-line)}
.career__item--now .career__node{border-color:var(--accent);background:var(--accent);
  box-shadow:0 0 0 3px var(--wash);
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
/* One ring leaves the stop as the pointer arrives, and fades. It grows by
   transform, 8px out on every side: the ring's box is the stop's 12px width
   and --career-len (12px and 8px a year) with 2px round it, so its two
   scales differ on a long stop. */
.career__node::after{content:"";position:absolute;inset:-2px;border-radius:inherit;
  border:1px solid var(--accent);opacity:0;--career-sx:2;
  --career-sy:calc((32 + 8 * var(--yrs)) / (16 + 8 * var(--yrs)))}
/* The stop's light: --link itself, the Research areas beads' light. It is
   out at rest and only lit while the route is laid (below). */
.career__node::before{content:"";position:absolute;inset:-2px;border-radius:inherit;
  background:var(--link);opacity:0}

/* The row's fill opens from its stop: it starts 8px left of the stop and
   runs to 12px past the text, behind everything in the list, so no stretch
   of the route passes under it. It is placed on the rail's grid line, so it
   follows the stop into either lane, but never closer than 6px to the
   dates. It opens by scaleX from its left edge, at the stop. */
.career__item::before{content:"";position:absolute;z-index:-1;
  grid-column:rail-start/-1;grid-row:1/-1;top:-12px;right:-12px;bottom:-12px;
  left:max(-6px,calc(var(--career-at) - var(--career-node) / 2 - 8px));
  border-radius:var(--r-md);background:var(--career-lit);opacity:0;
  transform:scaleX(0);transform-origin:0 50%}

/* A mouse or a trackpad only. (hover:hover) alone lets through a touch
   screen that reports hover, where a tap would leave a role lit. */
@media (hover:hover) and (pointer:fine){
  .career__item:hover::before{opacity:1;transform:none}
  .career__item:hover .career__track--lit{clip-path:inset(0)}
  .career__item:hover .career__node{border-color:var(--accent)}
  .career__item:hover .career__when{color:var(--accent)}
  /* one role at a time: the rest of the route steps back, and the present
     stretch and date give way until the pointer leaves the list */
  .career__list:has(.career__item:hover) .career__item:not(:hover) .career__rail{
    opacity:.45}
  .career__list:has(.career__item:hover) .career__item--now:not(:hover) .career__track--lit{
    clip-path:inset(100% 0 0 0)}
  .career__list:has(.career__item:hover) .career__item--now:not(:hover) .career__when{
    color:var(--muted)}
}
/* The entrance: one pen lays the route, from the present post down to the
   terminus, at the reader's pace. Its start state exists only on screen,
   without a reduced-motion request, on a list the script marked .is-out,
   and only for a role it has not laid yet: print, a page without scripts
   and reduced motion never see it. The words are never hidden.
   The script times each role (--career-d, -f, -t): the stop opens on the
   site's spring as the line reaches it (from 60% of its size; it never
   appears from nothing); 40ms on, the pen passes through it, and the stop
   fills with light from its top as it goes, at 55ms a year, so the seven
   years at Austin fill seven times as long as the year at Transtek; then
   the pen leaves the stop and runs down its stretch to the next one at an
   even 0.6px a millisecond, the turn between the lanes included (a wipe,
   top to bottom, so a curve is never squashed), while the light it left in
   the stop fades behind it. Only then does the next stop open, so the
   stretches of his career fill one after another in their order. The
   present stop opens with its amber ring, the line above it grows out of
   it, and the pen leaves it amber: the stretch that brought him back to a
   university. The terminus bar settles in last. Nothing waits for any of
   it: the fills and the wipes are fill-mode backwards only, so once a role
   is laid its states are the ones at rest and the pointer's. */
@media screen and (prefers-reduced-motion:no-preference){
  .career__item--now .career__rail::before{transform-origin:50% 100%}
  .career__list.is-out .career__item:not(.is-in) :is(.career__node,.career__fill,
    .career__track--rest){opacity:0}
  .career__list.is-out .career__item--now:not(.is-in) .career__track--lit,
  .career__list.is-out .career__item--now:not(.is-in) .career__rail::before,
  .career__list.is-out .career__item:not(.is-in) .career__track::after{opacity:0}
  .career__item.is-in :is(.career__node,.career__fill){
    animation:career-open var(--t-fast) var(--ease-state) var(--career-d,0ms) backwards,
      career-grow var(--spring-mid) var(--career-d,0ms) backwards}
  .career__item.is-in:not(.career__item--now) .career__node::before{
    animation:career-wipe var(--career-f,0ms) linear calc(var(--career-d,0ms) + 40ms)
        backwards,
      career-lamp var(--t-slow) var(--ease-state)
        calc(var(--career-d,0ms) + 40ms + var(--career-f,0ms)) backwards}
  .career__item.is-in:not(.career__item--now) .career__track--rest,
  .career__item--now.is-in .career__track--lit{
    animation:career-wipe var(--career-t,320ms) linear
      calc(var(--career-d,0ms) + 40ms + var(--career-f,0ms)) backwards}
  /* the blue under the present stretch waits for the amber to be in */
  .career__item--now.is-in .career__track--rest{animation:career-open 1ms linear
    calc(var(--career-d,0ms) + 40ms + var(--career-f,0ms) + var(--career-t,320ms)) backwards}
  .career__item.is-in:last-child .career__track::after{
    animation:career-open var(--t-fast) var(--ease-state)
        calc(var(--career-d,0ms) + 40ms + var(--career-f,0ms) + var(--career-t,320ms))
        backwards,
      career-bar var(--spring-mid)
        calc(var(--career-d,0ms) + 40ms + var(--career-f,0ms) + var(--career-t,320ms))
        backwards}
  .career__item--now.is-in .career__rail::before{
    animation:career-tail var(--spring-slow) calc(var(--career-d,0ms) + 120ms) backwards}
  .career__item--now.is-in .career__node::after{
    animation:career-hail 900ms var(--ease) calc(var(--career-d,0ms) + 120ms) forwards}
}
@keyframes career-open{from{opacity:0}}
@keyframes career-grow{from{transform:scale(.6)}}
@keyframes career-lamp{from{opacity:1}to{opacity:0}}
/* a stop's light and a stretch, uncovered from the top as the pen goes */
@keyframes career-wipe{from{clip-path:inset(0 0 100% 0)}to{clip-path:inset(0)}}
@keyframes career-bar{from{transform:scaleX(.3)}}
@keyframes career-tail{from{opacity:0;transform:scaleY(0)}}
/* the ring, under the pointer (career-ping) and as the present stop opens
   (career-hail): two names, so the stop can ring again for the pointer */
@keyframes career-ping{
  from{opacity:.55;transform:none}
  to{opacity:0;transform:scale(var(--career-sx),var(--career-sy))}
}
@keyframes career-hail{
  from{opacity:.55;transform:none}
  to{opacity:0;transform:scale(var(--career-sx),var(--career-sy))}
}
/* Arriving is drawn, leaving is quick. The fill opens out from the stop in
   240ms and fades out in 120ms; a stretch draws in --t-draw (360ms, the pace
   at which a topic card on the home page draws its fill) and gives way in
   160ms, so a pointer running down the list hands the light from one role
   to the next without a pause. A fill that fades is reset only once it is
   gone, so a pointer that comes straight back finds it where it was. */
@media (hover:hover) and (pointer:fine) and (prefers-reduced-motion:no-preference){
  .career__item::before{transition:opacity var(--t-quick) var(--ease-state),
    transform 0s linear var(--t-quick)}
  .career__item:hover::before{transition:opacity 0s,transform var(--spring-mid)}
  .career__rail{transition:opacity var(--t-fast) var(--ease-state)}
  .career__track--lit{transition:clip-path var(--t-fast) var(--ease-in-out)}
  .career__item:hover .career__track--lit,
  .career__item--now .career__track--lit{transition:clip-path var(--spring-draw)}
  .career__list:has(.career__item:hover) .career__item--now:not(:hover) .career__track--lit{
    transition:clip-path var(--t-fast) var(--ease-in-out)}
  .career__node{transition:border-color var(--t-fast) var(--ease-state)}
  .career__when{transition:color var(--t-fast) var(--ease-state)}
  /* the ring waits 60ms, so a pointer only passing over a role sets none off */
  .career__item:hover .career__node::after{
    animation:career-ping 700ms var(--ease) 60ms forwards}
  /* the present stop keeps its entrance ring in the list, so the pointer
     leaving it does not set that ring off again */
  .career__item--now.is-in:hover .career__node::after{
    animation:career-hail 900ms var(--ease) calc(var(--career-d,0ms) + 120ms) forwards,
      career-ping 700ms var(--ease) 60ms forwards}
}

/* 560px of section and up: dates | route | role. The items are subgrids, so
   the date column is as wide as the widest date in whatever font loaded; a
   browser without subgrid keeps an 80px column. */
@container career (min-width:560px){
  .career__list{--career-gap:36px;--career-dot:16px;--career-turn:48px;
    display:grid;grid-template-columns:max-content var(--career-rail) minmax(0,1fr);
    column-gap:12px}
  .career__item{grid-column:1/-1;column-gap:12px;align-items:baseline;
    grid-template-columns:80px var(--career-rail) minmax(0,1fr);
    grid-template-columns:subgrid;
    grid-template-areas:"when rail role" ". rail place" ". rail note"}
  .career__when{justify-self:end;text-align:right}
  .career__rail{align-self:stretch}
}

/* Under forced colours the route is CanvasText, and the lit stretch, the
   stops it fills and the present stop take Highlight. The row fill would be
   painted over with Canvas, so it goes. */
@media (forced-colors:active){
  .career__item::before,.career__node::before{display:none}
  .career__track--lit{color:Highlight}
  .career__node,.career__fill,.career__item--now .career__rail::before{
    forced-color-adjust:none}
  .career__node{border-color:CanvasText}
  .career__fill{background:Highlight}
  .career__item--now .career__node{background:Highlight;border-color:Highlight;
    box-shadow:none}
  .career__item--now .career__rail::before{border-color:Highlight}
}
@media (forced-colors:active) and (hover:hover) and (pointer:fine){
  .career__item:hover .career__node{border-color:Highlight}
}
@media print{
  .career h2{break-after:avoid}
  .career__item{break-inside:avoid}
}
"""
CSS = (CSS.replace("PADpx", "%dpx" % PAD).replace("LANEpx", "%dpx" % LANE)
       .replace("RAILpx", "%dpx" % RAIL))

# The route is laid in once, on the way down. It is hidden on the first
# scroll only if the section was below the screen when the page opened, so a
# page nobody scrolls never loses it, and a first scroll that lands on it (a
# page key, a long flick) still sees it laid. A role is laid when it comes
# into view, and every role above it first, so the pen always runs down the
# route in its order. Each role's times come from the route itself: its stop
# opens when the pen has finished the role above (--career-d), the pen dwells
# in the stop 55ms a year (--career-f; 180ms at the present stop, for its
# ring) and runs its stretch at 0.6px a millisecond (--career-t, from the
# stretch's measured height: the present one is the amber stretch, its stop
# included). The heights are all read before anything is written, so laying
# forces no layout. A watchdog lays any role on screen the observer has
# missed, once a second, until all are in. build.py wraps each part's script
# in its own scope.
JS = """
var list=document.querySelector('.career__list');
if(!list||!('IntersectionObserver' in window)||!window.matchMedia||
  !matchMedia('screen and (prefers-reduced-motion: no-preference)').matches)return;
var y0=scrollY;
addEventListener('scroll',function(){
  var items=[].slice.call(list.children),due=0,k=0;
  if(!items.length||items[0].getBoundingClientRect().top+scrollY-y0<innerHeight)return;
  var ms=function(el,n,v){el.style.setProperty('--career-'+n,Math.round(v)+'ms')},
    now=function(el){return el.classList.contains('career__item--now')},
    lay=function(it){
      var n=items.indexOf(it),h=items.slice(k,n+1).map(function(el){
        var tr=el.querySelector(now(el)?'.career__track--lit':'.career__track--rest');
        return tr?tr.getBoundingClientRect().height:0});
      for(var i=0;k<=n;k++,i++){
        var el=items[k],at=performance.now(),t=Math.max(at,due),w=h[i]/.6,
          f=now(el)?180:(parseFloat(el.style.getPropertyValue('--yrs'))||0)*55;
        ms(el,'d',t-at);ms(el,'f',f);ms(el,'t',w);
        el.classList.add('is-in');io.unobserve(el);due=t+f+w;
      }
    },
    io=new IntersectionObserver(function(es){es.forEach(function(e){
      if(e.isIntersecting)lay(e.target)})},{rootMargin:'0px 0px -12% 0px'}),
    dog=setInterval(function(){
      items.slice(k).forEach(function(it){var r=it.getBoundingClientRect();
        if(r.top<innerHeight&&r.bottom>0)lay(it)});
      if(k>=items.length)clearInterval(dog);
    },1000);
  list.classList.add('is-out');
  items.forEach(function(it){io.observe(it)});
},{once:true,passive:true});
"""


def _years(start, end):
    """A closed range: two time elements joined by a closed-up en dash."""
    return ('<time datetime="%d">%d</time>&#8211;<time datetime="%d">%d</time>'
            % (start, start, end, end))


BOGAZICI = "Bo&#287;azi&ccedil;i University"

# (role, first year, last year or None for the present, place, note, lane).
# Newest first. The words are unchanged from the earlier timeline: the role
# labels are ours, in the case he gives the posts in his biography; the two
# notes that start with "for" are his words from the deck. A place is a tuple
# of the parts a line may break between. The lane is ours too, read off the
# places: 1 for a university, 0 for a company. A stop's length comes from the
# two years, as whole years like the dates; the present post is a stop with
# no length yet.
ROLES = (
    ("Assistant Professor", 2026, None,
     ("Department of Civil Engineering", "Izmir Institute of Technology"), "", 1),
    ("Senior AI Engineer", 2024, 2026,
     ("Renesas Electronics America", "Maryland, USA"),
     "for acoustic wave-based vehicle monitoring solutions", 0),
    ("Applied Data Scientist", 2023, 2024,
     ("Transtek International Group", "Florida, USA"),
     "for bridge and road monitoring solutions", 0),
    ("Graduate Research Assistant", 2016, 2023,
     ("The University of Texas at Austin", "Texas, USA"),
     'Ph.D. <time datetime="2023">2023</time>', 1),
    ("Research Assistant", 2014, 2016,
     (BOGAZICI, "Istanbul, Turkey"),
     'M.Sc. <time datetime="2016">2016</time>', 1),
    ("Project Assistant", 2013, 2014,
     (BOGAZICI, "Istanbul, Turkey"),
     'B.S. <time datetime="2013">2013</time>', 1),
)

# the day he took up the present post, from his biography ("Since August 27, 2026")
SINCE = '<time datetime="2026-08-27">2026</time>'


def _place(parts):
    """Join a place's parts; each part stays whole on a line (.career__part)."""
    last = len(parts) - 1
    return " ".join('<span class="career__part">%s%s</span>'
                    % (part, "," if i < last else "")
                    for i, part in enumerate(parts))


def _turn(lane, below):
    """The S from this role's lane into the next role's, leaving and arriving
    upright. The box takes the turn's height from the CSS; the stroke keeps
    its width however far the box stretches. The attributes repeat the CSS so
    that a page read without its stylesheet shows a small line, not a
    300 by 150 black shape. The path's length is 1, so the entrance can draw
    it with a dash whatever its size."""
    a, b = PAD + lane * LANE, PAD + below * LANE
    return ('<svg viewBox="0 0 %d 48" width="%d" height="48" preserveAspectRatio="none" '
            'fill="none" stroke="currentColor" stroke-width="2" focusable="false">'
            '<path vector-effect="non-scaling-stroke" pathLength="1" '
            'd="M%d 0C%d 24 %d 24 %d 48"/>'
            '</svg>' % (RAIL, RAIL, a, a, b, b))


def render(**_kw):
    """Return the Career section as an HTML string.

    Each item opens with its role heading and the dates follow, so a screen
    reader moving by heading hears each role before its dates. The stylesheet
    places the dates, and the route is hidden from assistive technology: the
    words already say everything it draws.
    """
    items = []
    for i, (role, start, end, place, note, lane) in enumerate(ROLES):
        below = ROLES[i + 1][5] if i + 1 < len(ROLES) else lane
        turn = _turn(lane, below) if below != lane else ""
        dates = "Since " + SINCE if end is None else _years(start, end)
        cls = "career__item"
        cls += " career__item--now" if end is None else ""
        cls += " career__item--out" if lane == 0 else ""
        cls += " career__item--turn" if turn else ""
        items.append(
            '<li class="%s" style="--yrs:%d">'
            '<h3 class="career__role">%s</h3>'
            '<p class="career__when">%s</p>'
            '<p class="career__place">%s</p>%s'
            '<span class="career__rail" aria-hidden="true">'
            '<span class="career__track career__track--rest">%s</span>'
            '<span class="career__track career__track--lit">'
            '<span class="career__fill"></span>%s</span>'
            '<span class="career__node"></span></span>'
            '</li>' % (cls, 0 if end is None else end - start, role, dates,
                       _place(place),
                       '<p class="career__note">%s</p>' % note if note else "",
                       turn, turn))
    return ('<section class="career" aria-labelledby="career-title">'
            '<h2 id="career-title">Career</h2>'
            '<ol class="career__list" role="list">%s</ol>'
            '</section>' % "".join(items))
