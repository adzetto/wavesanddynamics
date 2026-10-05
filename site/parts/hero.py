# -*- coding: utf-8 -*-
"""hero: the home page hero, as his slide 1 lays it out.

The top of the page is his introduction beside the illustration: his name,
his numbered list and the two ways onward on the left, the city of
structures and models on the right (parts/heroart.py draws it; this module
gives it its place). Under them his "Myself:" paragraph runs at the reading
measure. Serif is his voice, sans is the interface. Every token is read from
parts/theme.py; none is written here.

His slide 1 has no photograph, and since round 5 neither has this page: his
portrait heads the column on every page (build.py's shell), so the hero no
longer draws it, nor the city and the address that stood under it. The
column and the footer give his department, institution and city; the
Contact page gives the address.

Layout follows the width of .hero2 (a size container), not the viewport:
  860px and up   his name, his list and the two controls beside the
                 illustration, in two equal columns (443px each at a 924px
                 column), the name's cap line level with the top of the
                 drawing. "Myself:" follows at --measure.
  under 860px    one column: name, list, controls, illustration (at most
                 640px), then "Myself:".
The markup order is that order at every width, so keyboard focus and a
screen reader meet his words and the ways onward before the drawing's keys.

"Myself:" heads his paragraph as "Motivation for Creating the Educational
Sections" heads the block after it. His slide sets the two labels alike, so
here both take the page's h2 (28/1.22, 47px over, 21px under): the paragraph
reads as the page's first section, not as a caption hanging from the hero.
His markup stays his: the label is his bold paragraph, restyled, and an
<h2> in its place takes the same rule.

The two controls close his introduction, and they open its first two items
one step deeper. About me is the brief's ghost button (DESIGN_BRIEF 1.4 and
6), a 1px --line-strong outline round an ink label that fills with --card
under a pointer. My research areas is a link-blue label with a 28px disc of
--card round its arrow. Under a mouse a capsule of the same --card fades in
over the whole control, growing its last 6% out of the disc's centre, so
the disc seems to open into it, while the arrow reaches forward: the head
moves 3px and the shaft grows with it. Everything that moves is transform,
opacity or stroke-dashoffset. Keyboard focus shows that end state at once,
without the travel; under reduced motion the capsule simply appears and the
arrow keeps still. A press takes the fill one step deeper, at once, and the
control gives a little under the finger; the module's only script is an
empty touch listener, without which iOS Safari shows no press at all.
"""

import re

__all__ = ["CSS", "JS", "render"]

CSS = """
/* ============================== home hero ============================== */
.hero2{container-type:inline-size}

/* the top of the page: his name, his list and the two ways onward, beside
   the illustration once the hero is 860px wide */
.hero2__top{display:grid;grid-template-columns:minmax(0,1fr);row-gap:40px;align-items:start}

/* ------------------------------------------------------------------ name */
/* The capitals start level with the top of the illustration beside them: in
   Source Serif 4 the cap line sits .25em under the top of the line box
   (measured at 32, 37 and 40px), and a -.25em margin lifts it there. Not
   text-box trimming: that trims to the cap height of whichever font is on
   screen, so the Georgia that stands in while the font loads made the name
   3.1px shorter and moved the whole hero when Source Serif 4 arrived. A
   margin in em moves nothing on the swap. */
.hero2__h1{margin:-.25em 0 0;font:600 clamp(32px,3.4vw,40px)/1.12 var(--serif);
  letter-spacing:-.014em;color:var(--ink);text-wrap:balance}

/* ------------------------------------------------------------- his words */
.hero2__intro{margin-top:24px}
.hero2__intro>p{margin:0;max-width:var(--measure);font:400 21px/1.52 var(--serif);
  letter-spacing:-.004em;color:var(--body)}
.hero2__intro ol{margin:12px 0 0;padding:0 0 0 28px;max-width:var(--measure)}
.hero2__intro ol>li{margin:6px 0 0;padding-left:4px;color:var(--ink)}
.hero2__intro ol>li::marker{font:600 15px var(--sans);
  font-variant-numeric:lining-nums tabular-nums;color:var(--accent)}
/* his sub-list hangs from a hairline under the Big Picture item: a tick on
   each line would read as a dash. Its four topics are linked like their
   parent, each to its own group on the Big Picture page. They are his
   subject matter, so what is not link in them takes the body colour, not
   the caption colour. */
.hero2 .hero2__intro ul{margin:6px 0 2px;padding:0 0 0 16px;list-style:none;
  border-left:1px solid var(--line)}
.hero2 .hero2__intro ul li{margin:0;padding:0;color:var(--body)}
.hero2 .hero2__intro ul li+li{margin-top:8px}
.hero2 .hero2__intro ul li::before{content:none}

/* ------------------------------------------------------ the illustration */
/* parts/heroart.py draws it and sizes it to this box; the box only places
   it. A figure keeps no default margin here. */
.hero2__art{min-width:0}
.hero2__art>figure{margin:0}

/* --------------------------------------------------------------- himself */
/* His paragraph at the reading measure, 47px under the hero's top block:
   the gap every h2 on the site takes over itself. */
.hero2__bio{margin-top:47px}
.hero2__bio p{margin:0;max-width:var(--measure);color:var(--body)}
.hero2__bio p+p{margin-top:12px}
/* The bold runs sit inside the paragraph's own line box: at the paragraph's
   leading the Georgia Bold that stands in for Source Serif 4 600 rides
   higher than the roman and would open a line by 1.6px, which the font swap
   then closes, moving the paragraph under it. */
.hero2__bio strong{font-weight:600;color:var(--ink);line-height:1}
/* "Myself:", his label, set as the page's h2 (DESIGN_BRIEF 2.2), as his
   slide sets it like "Motivation for Creating the Educational Sections".
   render() marks the block when it opens with his bold label paragraph; an
   h2 in its place takes the same rule. The paragraph follows 21px under it. */
.hero2__bio--head>p:first-child,.hero2__bio>h2:first-child{margin:0 0 21px;
  font:600 28px/1.22 var(--serif);letter-spacing:-.009em;color:var(--ink);
  text-wrap:balance}
.hero2__bio--head>p:first-child+p,.hero2__bio>h2:first-child+p{margin-top:0}

/* --------------------------------------------------------------- actions */
/* The two ways onward close his introduction, 32px under his list. They
   stand 12px apart, one gap for the row and for its wrap: when the pair
   wraps, as it does at 320px, the second starts on the text edge under the
   first. */
.hero2__act{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin-top:32px}
.hero2__btn,.hero2__more{position:relative;display:inline-flex;align-items:center;
  min-height:44px;border-radius:var(--r-pill);text-decoration:none;
  font:600 15px/1.2 var(--sans);letter-spacing:.01em;-webkit-tap-highlight-color:transparent}
/* About me, the ghost button (DESIGN_BRIEF 4, 6): its outline is the only
   border here that is an affordance, --line-strong at 3.49:1 */
.hero2__btn{padding:0 20px;color:var(--ink);background:transparent;
  border:1px solid var(--line-strong);
  transition:background-color var(--t-fast) var(--ease-state),
    border-color var(--t-fast) var(--ease-state),transform var(--spring-quick)}
/* My research areas: a link-blue label, its arrow in a 28px disc of --card
   8px in from the control's end. The capsule is the same --card under the
   whole control: hidden at rest, it fades in and grows from 94% to full
   size about the disc's centre, 22px in from the end, so the disc seems to
   open into it. --link is 6.31:1 on --card, --link-hover 9.19:1. */
.hero2__more{isolation:isolate;gap:6px;padding:0 8px 0 20px;color:var(--link);
  transition:color var(--t-fast) var(--ease-state),transform var(--spring-quick)}
.hero2__more::before{content:"";position:absolute;inset:0;z-index:-1;
  border-radius:inherit;background:var(--card);opacity:0;transform:scale(.94);
  transform-origin:calc(100% - 22px) 50%;
  transition:opacity var(--t-quick) var(--ease-state),transform var(--spring-quick)}
.hero2__go{flex:none;display:grid;place-items:center;width:28px;height:28px;
  border-radius:50%;background:var(--card)}
.hero2__go svg{display:block;overflow:visible}
/* The shaft is its own path, 3.6 units longer than it looks: its dash offset
   hides the end, so it can grow as the head moves (3.6 units is 3px at 20px) */
@media (prefers-reduced-motion:no-preference){
  .hero2__shaft{transition:stroke-dashoffset var(--spring-fast)}
  .hero2__head{transition:transform var(--spring-fast)}
}

/* ---------------------------------------------------------------- layout */
/* Wide: his list and the controls beside the illustration, in two equal
   columns (443px each at a 924px column). Measured in Chromium, his lede
   is 399px of type and his longer sub-line 698px, so at this width the
   lede keeps one line and the sub-line two with 10% to spare, and the
   Georgia that stands in while the font loads sets them the same: nothing
   below them moves when it swaps. The drawing keeps the top of its column,
   level with the name; his column, with the controls, runs on under it. */
@container (min-width:860px){
  .hero2--art .hero2__top{grid-template-columns:minmax(0,1fr) minmax(0,1.08fr);
    column-gap:clamp(32px,4cqi,56px);align-items:center}
  .hero2--art .hero2__art{margin-right:calc(-1 * clamp(0px,3cqi,40px))}
}
/* narrow: the illustration keeps a readable size and the text edge */
@container (min-width:560px) and (not (min-width:860px)){
  .hero2__art{max-width:640px}
}

/* ---------------------------------------------------------------- states */
/* Hover sits behind (hover:hover), so a tap never leaves one stuck. The
   ghost button fills with --card and its outline darkens to ink. On My
   research areas the label goes to --link-hover and the capsule opens in
   160ms (its growth in 240ms) while the arrow reaches in 240ms; letting go
   takes 120ms, the arrow 160ms. */
@media (hover:hover){
  .hero2__btn:hover{background:var(--card);border-color:var(--ink)}
  .hero2__more:hover{color:var(--link-hover)}
  .hero2__more:hover::before{opacity:1;transform:none;
    transition-duration:var(--t-fast),var(--t-mid)}
}
@media (hover:hover) and (prefers-reduced-motion:no-preference){
  .hero2__more:hover .hero2__shaft{stroke-dashoffset:0;transition-duration:var(--t-mid)}
  .hero2__more:hover .hero2__head{transform:translateX(3.6px);transition-duration:var(--t-mid)}
}
/* pressed: the fill one step deeper at once, --rule (the label on it is
   5.56:1, 5.15:1 dark), and the control gives a little under the finger */
.hero2__btn:active{background:var(--rule);border-color:var(--ink);
  transition-duration:0s,0s,var(--t-quick)}
.hero2__more:active::before{opacity:1;transform:none;background:var(--rule);transition:none}
.hero2__more:active .hero2__go{background:var(--rule)}
.hero2__btn:active,.hero2__more:active{transform:scale(.97)}
/* keyboard focus gets the hover's end state at once: no travel for a key */
.hero2 a:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.hero2__btn:focus-visible{background:var(--card);border-color:var(--ink);transition:none}
.hero2__more:focus-visible{color:var(--link-hover);transition:none}
.hero2__more:focus-visible::before{opacity:1;transform:none;transition:none}
@media (prefers-reduced-motion:no-preference){
  .hero2__more:focus-visible .hero2__shaft{stroke-dashoffset:0;transition:none}
  .hero2__more:focus-visible .hero2__head{transform:translateX(3.6px);transition:none}
}
/* reduced motion: the capsule is there or not, and nothing grows or shrinks */
@media (prefers-reduced-motion:reduce){
  .hero2__more::before{transform:none}
  .hero2__btn:active,.hero2__more:active{transform:none}
}
/* Windows contrast themes paint no fill: a system-colour edge marks both */
@media (forced-colors:active){
  .hero2__more{border:1px solid LinkText}
  .hero2__more::before{content:none}
}
"""

# iOS Safari applies :active only where a touch listener is registered, and
# the two controls turn off the grey tap flash, so without this a tap on either
# shows nothing before the page changes. The listener is empty and passive.
# build.py wraps each part's script in its own function scope.
JS = """
var hero=document.querySelector('.hero2');
if(hero)hero.addEventListener('touchstart',function(){},{passive:true});
"""

# ---------------------------------------------------------------------- his words
# Fallbacks only: build.py passes PROF_INTRO and PROF_BIO. These are character-
# for-character copies of those two strings, never a paraphrase.

_INTRO = """<p class="lede">This webpage introduces you to followings:</p>
<ol class="introlist">
 <li>Myself</li>
 <li>My Research</li>
 <li>Topics that I use in my research:
  <ul><li>In mechanic and physic side: wave propagation and dynamics</li>
      <li>In data side: AI, signal processing, system identification, optimization,
      estimation</li></ul></li>
</ol>"""

_BIO = """<p><strong>Myself:</strong></p>
<p>I am currently an Assistant Professor at Izmir Institute of Technology.
I performed product and service-oriented research and solutions on structural health
monitoring and non-destructive testing systems during his M.Sc. at Bogazici University
(Istanbul, Turkey, <span class="nw">2013-2016</span>) and Ph.D. at the University of Texas at
Austin (Texas, USA, <span class="nw">2016-2023</span>). Afterward, I worked in industry as
Applied Data Scientist at Transtek International Group (Florida, USA,
<span class="nw">2023-2024</span>) for bridge and road monitoring solutions, and as a senior
AI Engineer at Renesas Electronics America (Maryland, USA, <span class="nw">2024-2026</span>) for
acoustic wave-based vehicle monitoring solutions. During my career, I worked on tall
buildings, masonry buildings and bridges, suspension bridge, wind turbines, railway tracks,
and vehicles. Accordingly, I specialize on SHM, NDT and sound target analysis which are
deployed off-line through developed software and tools, cloud data processing or on-board
processing via microchips. Please see <a href="about.html">about me</a> section for detailed
information through my CV.</p>"""

# His label at the head of his biography: a paragraph that is one bold run,
# "<p><strong>Myself:</strong></p>". render() marks a biography that opens with
# it, so the CSS styles that paragraph as a heading and no other.
_LABEL = re.compile(r"\s*<p>\s*<strong>[^<]+</strong>\s*</p>")

# The arrow in the disc is drawn at the weight of its label, as a symbol set
# beside text should be. Source Sans 3 600 has a 115-unit stem, 1.73px at 15px;
# stroke 1.9 on the 24-unit grid at 20px is 1.58px, a shade under the stem, as
# a horizontal stroke is in the face itself. Two paths, so the shaft can grow
# while the head moves; the dash attributes keep it right even where the CSS
# is missing.
_ARROW = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" '
          'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
          'stroke-linejoin="round" aria-hidden="true">'
          '<path class="hero2__shaft" d="M5.75 12h14.6" stroke-dasharray="14.6" '
          'stroke-dashoffset="3.6"/>'
          '<path class="hero2__head" d="m13 7.75 4.25 4.25L13 16.25"/></svg>')


def render(contact=None, intro=None, bio=None, art=None):
    """Return the home page hero as an HTML string.

    intro, bio: HTML strings of his own words, inserted exactly as given.
    art: the illustration's markup (parts/heroart.py), placed beside his
         list; without it his list and the controls stand alone.
    contact: accepted so that build.py's call stands, and not drawn: since
         round 5 the home page carries no address (the column, the footer
         and the Contact page do).
    """
    intro = _INTRO if intro is None else intro
    bio = _BIO if bio is None else bio
    mode = "hero2--art" if art else "hero2--plain"
    beside = f'\n  <div class="hero2__art">{art}</div>' if art else ""
    head = " hero2__bio--head" if _LABEL.match(bio) else ""

    return f"""<section class="hero2 {mode}" aria-labelledby="hero2-title">
 <div class="hero2__top">
  <div class="hero2__lead">
   <h1 class="hero2__h1" id="hero2-title">Korkut Kaynardag, PhD</h1>
   <div class="hero2__intro">{intro}</div>
   <div class="hero2__act">
    <a class="hero2__btn" href="about.html">About Me</a>
    <a class="hero2__more" href="research.html">My Research Areas<span class="hero2__go">{_ARROW}</span></a>
   </div>
  </div>{beside}
 </div>
 <div class="hero2__bio{head}">{bio}</div>
</section>"""
