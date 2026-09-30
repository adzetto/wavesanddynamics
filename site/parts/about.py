# -*- coding: utf-8 -*-
"""About Me: the profile, his biography, his research areas, Career, At a glance.

render_page(about_html, links, areas, timeline_html) returns the whole page
body, the .wrap container included, as build.py's page_about() did:

  H1 "About Me"
  the profile: portrait, "Korkut Kaynardag, PhD", his post, and under it the
    actions row, at the top as the client asked: Download CV to cv.html (the
    site's one filled button, which DESIGN_BRIEF.md 6 keeps for the CV), then
    Google Scholar, LinkedIn and ResearchGate, then GitHub and YouTube a step
    quieter
  two columns from 800px of content width:
    left   "Biography": his PROF_ABOUT, with the eight runs he set in bold on
           slide 2 in bold here too
    right  "Research areas": the list from his CV, whole and above the fold at
           1280x800, and a link to My Research Areas. It stays in view while
           the biography scrolls past it, where the window is tall enough
  Career (parts/timeline.py), then "At a glance" below it: his three figures,
    each a way into the section of the CV that lists them.

His words: about_html goes in as given. If it lacks the bold runs, embolden()
puts <strong> round his exact words and nothing else, so the text a reader
gets is unchanged. The areas are his CV's words, escaped and nothing more.

Motion. The areas are a chain of beads on one dotted thread, the home page's
sensors strung together. Each time the chain comes into view (as the page
opens, and again whenever it has left the screen and comes back) a signal runs
down it: the thread lights from bead to bead, each bead fills as the light
reaches it and lets it go, and the first and the last bead send out one ring.
Under a mouse or a trackpad the bead beside the pointer fills and swells, the
thread carries the light out to the beads on either side and they answer as
it arrives; moving down the list moves that lit window along the chain.
Nothing is hidden before any of this and nothing waits for it: every state is
laid over the chain at rest and goes back to it. Under reduced motion no
signal runs and the pointer's states change in place. The glance figures
arrive once on the way down: each hairline draws, and each figure comes up
out of its own line and settles on the slow spring, sharpening as it slows.
Under the pointer a figure's fill unrolls down from its hairline; a press
deepens it and the card gives a little.

Scoped under .abt and .glance. Tokens are read, never written. No side
effects on import. Type, measure and numerals follow DESIGN_BRIEF.md 2.2 to
2.4; the hover vocabulary is section 4.
"""

import html as _html
import re
from html.entities import codepoint2name, html5

__all__ = ["CSS", "JS", "FIGURES", "BOLD", "CV_HREF", "embolden", "render_page",
           "render_glance", "render_timeline"]

# where Download CV and the three figures lead: the CV page (parts/cv.py),
# whose sections carry cv.json's ids
CV_HREF = "cv.html"

CSS = """
/* ===================== About: the page ===================== */
.abt__h1{margin:0 0 28px}

/* --------------------------------------------------------------- profile */
/* Portrait and name side by side, the name's cap line level with the top of
   the picture. The portrait is the home page's file at 120px: the home page
   shows it at 280, so here it is a byline, not a hero. */
.abt__card{display:grid;grid-template-columns:120px minmax(0,1fr);column-gap:24px;
  align-items:start}
.abt__portrait{display:block;width:120px;height:auto;aspect-ratio:4/5;object-fit:cover;
  border-radius:var(--r-md);background:var(--card)}
.abt__name{margin:0;font:600 26px/1.2 var(--serif);letter-spacing:-.008em;
  color:var(--ink);text-wrap:balance;text-box:trim-start cap alphabetic}
@supports not (text-box:trim-start cap alphabetic){.abt__name{margin-top:-.22em}}
.abt__post{margin:12px 0 0;font:400 15px/1.5 var(--sans);letter-spacing:.006em;
  color:var(--ink)}
.abt__post span{display:block;color:var(--muted)}

/* --------------------------------------------------------------- actions */
/* Download CV, then the profiles beside it. The list takes what is left of
   the row and wraps inside itself, so its second line starts under its
   first, never under the button. */
.abt__act{display:flex;flex-wrap:wrap;align-items:flex-start;gap:12px 24px;
  margin:28px 0 0}
/* the one filled button on the site: warm means action (DESIGN_BRIEF.md 1.4).
   White on --accent 5.55:1, on its hover 6.85:1, pressed 8.35:1 */
.abt__cv{flex:none;display:inline-flex;align-items:center;gap:8px;min-height:44px;
  padding:0 20px 0 16px;border-radius:var(--r-pill);background:var(--accent);
  color:var(--btn-fg);font:600 15px/1.2 var(--sans);letter-spacing:.01em;
  text-decoration:none;-webkit-tap-highlight-color:transparent;
  transition:background-color var(--t-fast) var(--ease-state),
    transform var(--spring-quick)}
.abt__cv svg{flex:none;display:block}
.abt__cv:active{background:var(--accent-press);transform:scale(.97)}
.abt__cv:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.abt__links{flex:1 1 240px;display:flex;flex-wrap:wrap;align-items:center;gap:0 20px;
  margin:0;padding:0;list-style:none}
.abt__links li{margin:0}
.abt__links a{display:inline-flex;align-items:center;gap:3px;min-height:44px;
  font:600 15px/1.2 var(--sans);letter-spacing:.01em;color:var(--link);
  -webkit-tap-highlight-color:transparent}
/* GitHub and YouTube: the same links, a step quieter (--muted 5.10:1) */
.abt__links .abt__also a{color:var(--muted);font-weight:400}
.abt__ext{flex:none;display:block;overflow:visible}
/* The arrow leans out a little further under the pointer: its head moves 2
   units up and away while its shaft grows to meet it. The dash hides the
   shaft's last 2.83 units (2 across, 2 up) at rest. */
.abt__eshaft{stroke-dasharray:15.56;stroke-dashoffset:2.83}

/* ------------------------------------------------------------- the columns */
/* The areas follow the actions in the markup, so wherever the page is one
   column they come straight after the profile, before the biography: the
   client wants them seen as the page opens. From 800px of content width
   they move to their own column on the right. */
.abt__cols{container:abt/inline-size}
.abt__grid{display:grid;grid-template-columns:minmax(0,1fr);align-items:start}
.abt__areas{margin-top:40px}
/* the profile links' 44px targets already leave 14px under their text */
.abt__bio h2{margin:36px 0 18px}
.abt__bio p{max-width:var(--measure)}
.abt__bio p:last-child{margin-bottom:0}
.abt__bio strong{font-weight:600;color:var(--ink)}

/* ------------------------------------------------------------ research areas */
/* Serif, because they are his words; 16px, so the longest of them ("Signal
   Processing and Noise Reduction", 288px) keeps to one line in the column.
   Beside each area a bead sits on one dotted thread, the way the home page's
   drawing strings its sensors together. Thread and beads are --link taken
   45% into the paper, the Career route's blue: drawing, not information.
   Lit, the thread takes --link 80% and a bead --link itself. */
.abt__areas{--abt-line:var(--line-strong);--abt-lit:var(--link);--abt-hot:var(--link)}
@supports (color:color-mix(in oklab,red,blue)){
  .abt__areas{--abt-line:color-mix(in oklab,var(--link) 45%,var(--page));
    --abt-lit:color-mix(in oklab,var(--link) 80%,var(--page))}
}
/* trimmed to its cap line, as the name is, so the two tops sit level with the
   portrait's */
.abt__areas h2{margin:0 0 14px;font:600 12px/1.1 var(--sans);letter-spacing:.12em;
  text-transform:uppercase;color:var(--muted);text-box:trim-start cap alphabetic}
/* its own stacking context: the beads sit over the lit thread and under
   nothing else on the page */
.abt__list{position:relative;isolation:isolate;margin:0;padding:0 0 0 24px;
  list-style:none}
/* the thread at rest, dotted, from the first bead's centre to the last one's */
.abt__list::before{content:"";position:absolute;left:4px;top:16px;bottom:16px;width:1px;
  background:repeating-linear-gradient(to bottom,var(--abt-line) 0 2px,transparent 2px 6px)}
.abt__list li{position:relative;margin:0;padding:5px 0;font:400 16px/1.35 var(--serif);
  color:var(--ink)}
/* a bead: a ring with the paper inside, so the thread runs behind it. Its
   light (::before) and one ring of its own (::after) wait out of sight. */
.abt__bead{position:absolute;z-index:1;left:-24px;top:12px;width:9px;height:9px;
  box-sizing:border-box;border:1.5px solid var(--abt-line);border-radius:var(--r-pill);
  background:var(--page)}
.abt__bead::before,.abt__bead::after{content:"";position:absolute;inset:-1.5px;
  border-radius:inherit;opacity:0}
.abt__bead::before{background:var(--abt-hot)}
.abt__bead::after{border:1px solid var(--abt-hot)}
/* The lit thread from a bead to the next one, over the dotted one: ::before
   carries the signal down the chain, ::after the pointer's light. At rest
   both are drawn to nothing. The last bead has no next one. */
.abt__list li::before,.abt__list li::after{content:"";position:absolute;left:-20px;
  top:16.5px;width:1px;height:100%;background:var(--abt-lit);transform:scaleY(0);
  transform-origin:50% 0}
.abt__list li:last-child::before,.abt__list li:last-child::after{content:none}
.abt__more{display:inline-flex;align-items:center;gap:4px;min-height:44px;
  margin:12px 0 0 24px;font:600 15px/1.2 var(--sans);letter-spacing:.01em;
  color:var(--link);text-decoration:none;-webkit-tap-highlight-color:transparent}
.abt__more span{text-decoration-line:underline;text-decoration-thickness:1.5px;
  text-underline-offset:3px;text-decoration-color:transparent;
  transition:text-decoration-color var(--t-fast) var(--ease-state)}
.abt__more svg{flex:none;display:block;overflow:visible}
.abt__shaft{stroke-dasharray:13;stroke-dashoffset:5}

/* A tablet's width, or a laptop's beside the open column: the areas in two
   columns under the profile, each with its ring and no line, so all fifteen
   and the start of the biography share the first screen. The exact
   complement of the wide query: a min/max pair would overlap by 1/64px. */
@container abt (min-width:560px) and (not (min-width:800px)){
  .abt__list{columns:2;column-gap:32px}
  .abt__list::before,.abt__list li::before,.abt__list li::after{content:none}
  .abt__list li{break-inside:avoid}
}
/* Two columns once the biography keeps about 460px beside the areas. The
   areas' column is as wide as its longest line; the biography takes the
   rest, up to the measure. */
@container abt (min-width:800px){
  .abt__grid{grid-template-columns:minmax(0,var(--measure)) auto;
    grid-template-rows:auto 1fr;column-gap:32px;justify-content:space-between}
  .abt__top{grid-column:1;grid-row:1}
  .abt__bio{grid-column:1;grid-row:2}
  .abt__areas{grid-column:2;grid-row:1/span 2;margin-top:0}
}
/* Where the column is on screen and the window can hold the whole list, the
   areas stay beside the biography as it scrolls past them. */
@media (width > 1000px) and (min-height:680px){
  @container abt (min-width:800px){
    .abt__areas{position:sticky;top:40px}
  }
}

/* ---------------------------------------------------------------- states */
@media (hover:hover){
  .abt__cv:hover{background:var(--accent-hover)}
  .abt__cv:active{background:var(--accent-press)}
  .abt__more:hover span{text-decoration-color:currentColor}
}
/* A mouse or a trackpad (a touch screen that reports hover would keep a
   tapped bead lit): the bead beside the pointer fills and swells, the thread
   lights out to the beads on either side, and they answer as the light
   reaches them. A pointer running down the list moves that window along the
   chain. The words do not move. */
@media (hover:hover) and (pointer:fine){
  .abt__list li:hover .abt__bead{border-color:var(--abt-hot);background:var(--abt-hot);
    transform:scale(1.33)}
  .abt__list li:hover::after{transform:none}
  .abt__list li:has(+ li:hover)::after{transform:none;transform-origin:50% 100%}
  .abt__list li:hover + li .abt__bead,
  .abt__list li:has(+ li:hover) .abt__bead{border-color:var(--abt-lit);
    transform:scale(1.15)}
}
/* in two columns there is no thread, and the next bead may head the other
   column: the pointer's bead answers alone */
@media (hover:hover) and (pointer:fine){
  @container abt (min-width:560px) and (not (min-width:800px)){
    .abt__list li:hover + li .abt__bead,
    .abt__list li:has(+ li:hover) .abt__bead{border-color:var(--abt-line);transform:none}
  }
}
@media (prefers-reduced-motion:no-preference){
  .abt__eshaft,.abt__shaft{transition:stroke-dashoffset var(--spring-fast)}
  .abt__ehead,.abt__head{transition:transform var(--spring-fast)}
  /* The signal. Each time the chain comes into view the script marks it
     .is-run, and after a breath a light runs down it at 60ms a bead, a
     signal's even pace: the thread lights from each bead to the next, each
     bead fills as the light reaches it, swells a little past its ring and
     lets the light go, and the thread goes out two beads behind the light,
     so three or four beads are lit at a time. The first bead and the last
     one each send out a ring. The run is over 2s after it starts. Taking
     .is-run away, once the chain has left the screen, takes the run with
     it, ready to go again. */
  .abt__list{--abt-lead:var(--t-mid);--abt-step:60ms}
  .abt__list.is-run .abt__bead::before{animation:abt-flash 520ms var(--ease)
    calc(var(--abt-lead) + var(--i,0) * var(--abt-step)) both}
  .abt__list.is-run li::before{
    animation:abt-draw var(--abt-step) linear
        calc(var(--abt-lead) + var(--i,0) * var(--abt-step)) both,
      abt-wane var(--t-draw) var(--ease-state)
        calc(var(--abt-lead) + (var(--i,0) + 2) * var(--abt-step)) both}
  /* :where() keeps this lighter than the pointer's ring below, so the
     first and last bead still answer the pointer after the run */
  .abt__list.is-run :where(li:first-child,li:last-child) .abt__bead::after{
    animation:abt-call 900ms var(--ease)
      calc(var(--abt-lead) + var(--i,0) * var(--abt-step)) forwards}
}
@media (hover:hover) and (prefers-reduced-motion:no-preference){
  .abt__links a:hover .abt__eshaft{stroke-dashoffset:0;transition-duration:var(--t-mid)}
  .abt__links a:hover .abt__ehead{transform:translate(2px,-2px);
    transition-duration:var(--t-mid)}
  .abt__more:hover .abt__shaft{stroke-dashoffset:0;transition-duration:var(--t-mid)}
  .abt__more:hover .abt__head{transform:translateX(5px);
    transition:transform var(--spring-mid) 60ms}
}
/* Arriving is drawn, leaving is quick. The bead swells in 240ms and turns
   its colours in 120ms; the thread runs out to the neighbours in 240ms and
   goes back in 120ms toward the bead it came from (its origin holds until
   it is gone), and the neighbours answer 120ms late, as the light reaches
   them. One faint ring leaves the bead 60ms after the pointer arrives, so a
   pointer only passing over it sets none off. */
@media (hover:hover) and (pointer:fine) and (prefers-reduced-motion:no-preference){
  .abt__bead{transition:transform var(--spring-fast),
    border-color var(--t-quick) var(--ease-state),
    background-color var(--t-quick) var(--ease-state)}
  .abt__list li:hover .abt__bead{transition-duration:var(--t-mid),var(--t-quick),
    var(--t-quick)}
  .abt__list li:hover + li .abt__bead,
  .abt__list li:has(+ li:hover) .abt__bead{transition-delay:var(--t-quick)}
  .abt__list li::after{transition:transform var(--t-quick) var(--ease-state),
    transform-origin 0s linear var(--t-quick)}
  .abt__list li:hover::after,.abt__list li:has(+ li:hover)::after{
    transition:transform var(--spring-mid),transform-origin 0s}
  .abt__list li:hover .abt__bead::after{animation:abt-ping 700ms var(--ease) 60ms forwards}
}
/* Keyboard focus gets the hover's end state at once: no travel for a key.
   These come after the hover rules and match them in weight, so a link both
   hovered and focused takes them. */
.abt__more:focus-visible span{text-decoration-color:currentColor;transition:none}
@media (prefers-reduced-motion:no-preference){
  .abt__links a:focus-visible .abt__eshaft{stroke-dashoffset:0;transition:none}
  .abt__links a:focus-visible .abt__ehead{transform:translate(2px,-2px);transition:none}
  .abt__more:focus-visible .abt__shaft{stroke-dashoffset:0;transition:none}
  .abt__more:focus-visible .abt__head{transform:translateX(5px);transition:none}
}
/* a bead's light: it fills, swells a little past its ring, settles and lets
   the light go */
@keyframes abt-flash{
  0%{opacity:0;transform:scale(.5)}
  15%{opacity:1;transform:scale(1.25)}
  35%{opacity:1;transform:none}
  100%{opacity:0;transform:none}
}
@keyframes abt-draw{from{transform:scaleY(0)}to{transform:none}}
@keyframes abt-wane{from{opacity:1}to{opacity:0}}
/* one ring leaving a bead: where the signal sets out and where it arrives
   (abt-call), and under the pointer (abt-ping). Two names, so a bead the
   signal has called can still answer the pointer. */
@keyframes abt-call{from{opacity:.5;transform:none}to{opacity:0;transform:scale(2.6)}}
@keyframes abt-ping{from{opacity:.5;transform:none}to{opacity:0;transform:scale(2.2)}}
/* Reduced motion: the site's arrow stands finished, shaft drawn and head at
   home (DESIGN_BRIEF.md 4.1); the leaning arrow keeps its rest shape, whose
   shaft already meets its head; the button does not give under a press. */
@media (prefers-reduced-motion:reduce){
  .abt__cv:active{transform:none}
  .abt__shaft{stroke-dashoffset:0}
}
/* Windows contrast themes paint no fill: the button keeps an edge, the
   thread and the beads take the text colour and the lights go; the bead
   beside the pointer takes Highlight */
@media (forced-colors:active){
  .abt__cv{border:1px solid ButtonText}
  .abt__list::before{background:CanvasText;forced-color-adjust:none;width:1px}
  .abt__bead{border-color:CanvasText}
  .abt__bead::before,.abt__bead::after,.abt__list li::before,
  .abt__list li::after{display:none}
}
@media (forced-colors:active) and (hover:hover) and (pointer:fine){
  .abt__list li:hover .abt__bead{forced-color-adjust:none;border-color:Highlight;
    background:Highlight}
}
@media print{
  .abt__areas{position:static}
  .abt__cv{border:1px solid currentColor;background:none;color:inherit}
  .abt__bead::before,.abt__bead::after,.abt__list li::before,
  .abt__list li::after{display:none}
}
"""

# iOS Safari shows :active only where a touch listener is registered; this
# one is empty and passive. The chain's signal runs each time the chain comes
# into view: when its top is on screen with 30% of it, or when 90% of it is
# (coming back from above, the top shows last). It is taken away once the
# chain has left the screen, ready to run again. build.py wraps each part's
# script in its own scope.
JS = """
var abt=document.querySelector('.abt');
if(abt)abt.addEventListener('touchstart',function(){},{passive:true});
var chain=document.querySelector('.abt__list');
if(chain&&'IntersectionObserver' in window&&window.matchMedia&&
  matchMedia('(prefers-reduced-motion: no-preference)').matches){
  new IntersectionObserver(function(es){
    var e=es[es.length-1],r=e.intersectionRatio,
      top=e.boundingClientRect.top>=(e.rootBounds?e.rootBounds.top:0)-1;
    if(!e.isIntersecting)chain.classList.remove('is-run');
    else if(r>=.9||top&&r>=.3)chain.classList.add('is-run');
  },{threshold:[0,.3,.6,.9]}).observe(chain);
}
"""

# ---------------------------------------------------------------- his words

# The runs he set in bold in the About text of his deck (slide 2), exactly as
# the slide spells them. embolden() finds each in about_html whatever the
# markup does with its spaces, line breaks and accented letters.
BOLD = ("master's degrees", "Boğaziçi University in 2013 and 2016",
        "Ph.D.", "The University of Texas at Austin in 2023",
        "Applied Data Scientist at Transtek International Group",
        "Senior AI Engineer at Renesas Electronics America",
        "Assistant Professor", "Izmir Institute of Technology")


def _char(ch):
    """A pattern for one character of a run as it may stand in HTML source."""
    if ch.isspace():
        return r"\s+"
    forms = {re.escape(ch)}
    cp = ord(ch)
    if cp > 126 or ch in "'&\"":
        forms.add("&#0*%d;" % cp)
        forms.add("(?i:&#x0*%x;)" % cp)
        if cp in codepoint2name:
            forms.add("&%s;" % codepoint2name[cp])
        forms.update("&" + re.escape(n) for n, v in html5.items()
                     if v == ch and n.endswith(";"))
    return "(?:%s)" % "|".join(sorted(forms, key=len, reverse=True))


def _state(src, pos):
    """(inside a tag, inside a bold run) at pos in src."""
    before = src[:pos]
    in_tag = before.rfind("<") > before.rfind(">")
    opened = [m.end() for m in re.finditer(r"<(?:strong|b)(?:\s[^>]*)?>", before, re.I)]
    closed = [m.end() for m in re.finditer(r"</(?:strong|b)\s*>", before, re.I)]
    in_bold = bool(opened) and (not closed or opened[-1] > closed[-1])
    return in_tag, in_bold


def embolden(src, runs=BOLD):
    """Put <strong> round the first plain occurrence of each run in src.

    A run already inside <strong> or <b> is left alone, so markup that carries
    the bold itself passes through unchanged. Only tags are added: the text a
    reader gets is the same, character for character.
    """
    for run in runs:
        pat = re.compile("".join(_char(c) for c in run))
        for m in pat.finditer(src):
            in_tag, in_bold = _state(src, m.start())
            if in_tag or in_bold:
                continue
            src = "%s<strong>%s</strong>%s" % (src[:m.start()], m.group(0), src[m.end():])
            break
    return src


# ------------------------------------------------------------------ fallbacks

# Used only when build.py passes None: the five profiles and the fifteen areas
# as his CV (content/source/Korkut_Kaynardag_Resume.docx) gives them. The
# live values come from content/cv/cv.json.
_LINKS = (
    {"label": "Google Scholar", "kind": "scholar",
     "href": "https://scholar.google.com/citations?user=v_eQpwUAAAAJ&hl=en"},
    {"label": "LinkedIn", "kind": "linkedin",
     "href": "https://www.linkedin.com/in/korkutkaynardag/"},
    {"label": "ResearchGate", "kind": "researchgate",
     "href": "https://www.researchgate.net/profile/Korkut-Kaynardag"},
    {"label": "GitHub", "kind": "github", "href": "https://github.com/korkutphd"},
    {"label": "YouTube", "kind": "youtube",
     "href": "https://www.youtube.com/@korkutkaynardag9147"},
)
_AREAS = (
    "Structural Health Monitoring", "Non-Destructive Testing",
    "Real-Time Automated Monitoring", "Contact and Non-Contact Sensing",
    "Connected Vehicles", "Vehicle and Structural Dynamics",
    "Acoustic Wave Propagation", "System Identification",
    "Data Science and Machine Learning", "Predictive Maintenance",
    "Digital Twins and Optimization", "Analytical and Numerical Modeling",
    "Structural Reliability and Resiliency", "Signal Processing and Noise Reduction",
    "Cloud and Embedded Engineering",
)

# the profiles in the order the actions row shows them; the last two are the
# quieter pair (his CV lists them after the other three, as does the spec)
_PRIMARY = ("scholar", "linkedin", "researchgate")
_SECONDARY = ("github", "youtube")
_DEFAULT_LABEL = {"scholar": "Google Scholar", "linkedin": "LinkedIn",
                  "researchgate": "ResearchGate", "github": "GitHub",
                  "youtube": "YouTube"}

# ---------------------------------------------------------------------- glyphs

# His deck marks Download CV with a curriculum vitae: a sheet with a head and
# shoulders and a line of text. The inline family: 24-unit grid at 20px,
# stroke 1.5 (DESIGN_BRIEF.md 7.1), four strokes.
_CV = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
       'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
       '<rect x="5.25" y="3.25" width="13.5" height="17.5" rx="2.25"/>'
       '<circle cx="12" cy="9" r="2.25"/>'
       '<path d="M8.6 14.6c.62-1.46 1.8-2.2 3.4-2.2s2.78.74 3.4 2.2"/>'
       '<path d="M9.25 17.5h5.5"/></svg>')

# Off to another site: the arrow leans up and away. Drawn on the 24 grid at
# 16px with stroke 1.9, 1.27px on screen, the inline family's weight. The
# shaft runs 2 units past the head's corner; the CSS hides that end at rest.
_EXT = ('<svg class="abt__ext" viewBox="0 0 24 24" width="16" height="16" fill="none" '
        'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true">'
        '<path class="abt__eshaft" d="M7.5 16.5 18.5 5.5"/>'
        '<path class="abt__ehead" d="M10 7.5h6.5v6.5"/></svg>')

# the site's arrow (build.py's ARROW): two paths, so the shaft can draw while
# the head travels
_ARROW = ('<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" '
          'stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round" '
          'aria-hidden="true"><path class="abt__shaft" d="M3.5 12h13"/>'
          '<path class="abt__head" d="m11.5 6.8 5.2 5.2-5.2 5.2"/></svg>')


def _e(text):
    return _html.escape(str(text), quote=True)


def _profiles(links):
    """(primary, secondary) lists of (label, href): http(s) links only, and
    never this site itself (his CV lists it as his personal webpage)."""
    links = _LINKS if links is None else links
    by_kind, extra = {}, []
    for ln in links or ():
        href = str(ln.get("href") or "").strip()
        if not re.match(r"https?://", href, re.I) or "wavesanddata.com" in href.lower():
            continue
        kind = str(ln.get("kind") or "").strip().lower()
        label = str(ln.get("label") or "").strip() or _DEFAULT_LABEL.get(kind) or href
        if kind in _PRIMARY or kind in _SECONDARY:
            by_kind.setdefault(kind, (label, href))
        else:
            extra.append((label, href))
    primary = [by_kind[k] for k in _PRIMARY if k in by_kind]
    secondary = [by_kind[k] for k in _SECONDARY if k in by_kind] + extra
    return primary, secondary


def _actions(links):
    primary, secondary = _profiles(links)
    items = "".join('<li><a href="%s" rel="me">%s%s</a></li>' % (_e(h), _e(t), _EXT)
                    for t, h in primary)
    items += "".join('<li class="abt__also"><a href="%s" rel="me">%s%s</a></li>'
                     % (_e(h), _e(t), _EXT) for t, h in secondary)
    ul = '<ul class="abt__links" aria-label="Profiles">%s</ul>' % items if items else ""
    return ('<div class="abt__act">'
            '<a class="abt__cv" href="%s">%s<span>Download CV</span></a>%s'
            '</div>' % (CV_HREF, _CV, ul))


def _areas(areas):
    areas = [a for a in (_AREAS if areas is None else areas or ()) if str(a).strip()]
    if not areas:
        return ""
    items = "".join('<li style="--i:%d"><span class="abt__bead" aria-hidden="true"></span>'
                    '%s</li>' % (i, _e(str(a).strip())) for i, a in enumerate(areas))
    return ('<aside class="abt__areas" aria-labelledby="abt-areas">'
            '<h2 id="abt-areas">Research areas</h2>'
            '<ul class="abt__list" role="list">%s</ul>'
            '<a class="abt__more" href="research.html"><span>My Research Areas</span>%s</a>'
            '</aside>' % (items, _ARROW))


def render_page(about_html, links=None, areas=None, timeline_html=None):
    """Return the About page body as an HTML string.

    about_html     his PROF_ABOUT, inserted as given apart from the bold runs
                   (embolden(), a no-op when the markup already has them)
    links          cv.json's links: dicts with label, href and kind (scholar,
                   linkedin, researchgate, github, youtube). None: his CV's
    areas          cv.json's areas, his words. None: his CV's
    timeline_html  the Career section. None or "": parts/timeline.py's
    """
    career = timeline_html or render_timeline()
    return (
        '<div class="wrap abt">'
        '<h1 class="abt__h1">About Me</h1>'
        '<div class="abt__cols"><div class="abt__grid">'
        '<div class="abt__top">'
        '<div class="abt__card">'
        '<img class="abt__portrait" src="portrait.webp" alt="Korkut Kaynardag" '
        'srcset="portrait-280.webp 280w, portrait.webp 520w" sizes="120px" '
        'width="520" height="650" decoding="async">'
        '<div class="abt__who">'
        '<h2 class="abt__name">Korkut Kaynardag, PhD</h2>'
        '<p class="abt__post">Assistant Professor '
        '<span>Department of Civil Engineering</span> '
        '<span>Izmir Institute of Technology</span></p>'
        '</div></div>'
        '%s'
        '</div>'
        '%s'
        '<section class="abt__bio" aria-labelledby="abt-bio">'
        '<h2 id="abt-bio">Biography</h2>%s</section>'
        '</div></div>'
        '%s%s'
        '</div>' % (_actions(links), _areas(areas), embolden(about_html or ""),
                    career, render_glance()))


# ------------------------------------------------------------------ At a glance

CSS += """
/* ===================== About: at a glance ===================== */
/* Three figures on the paper, each under one --rule hairline: no fill, no
   border box, no shadow. Each is a way into the CV section that lists what
   it counts, so each answers the pointer as a card does on this site
   (DESIGN_BRIEF.md 4): a 4% ink fill hung from the hairline and bled 12px
   past the words, the label underlined, the arrow drawn. Nothing lifts. The
   list is the query container. Narrow, a figure is one row with its label
   on the numeral's baseline; from 740px the figures sit three across. */
.glance{margin:47px 0 0}
.glance__head{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 12px;
  margin:0 0 21px}
.glance__title{margin:0}                   /* the page's h2, set in theme.py */
.glance__when{margin:0;font:600 14px/1.5 var(--sans);letter-spacing:.01em;
  color:var(--muted);font-variant-numeric:lining-nums proportional-nums}
.glance__grid{container:glance/inline-size;display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));column-gap:40px;
  margin:0;padding:0;list-style:none}
/* margin:0 against style.css's li{margin:.35em 0}: grid items do not collapse
   margins */
.glance__card{grid-column:1/-1;position:relative;margin:0}
.glance__card::before{content:"";position:absolute;top:0;left:0;right:0;z-index:1;
  border-top:1px solid var(--rule);transform-origin:0 50%}
.glance__a{position:relative;isolation:isolate;display:grid;
  grid-template-columns:minmax(44px,max-content) minmax(0,1fr);
  column-gap:16px;align-items:baseline;margin:0 -12px;padding:20px 12px;
  border-radius:0 0 var(--r-md) var(--r-md);color:inherit;text-decoration:none;
  -webkit-tap-highlight-color:transparent}
/* the fill, hung from the hairline: it unrolls down the card from it under
   the pointer, and is simply there for a key or a press */
.glance__a::before{content:"";position:absolute;inset:0;z-index:-1;
  border-radius:inherit;background:var(--surface);
  background:color-mix(in oklab,var(--ink) 4%,var(--page));
  opacity:0;transform:scaleY(0);transform-origin:50% 0}
/* 400, not 600: at 40px the optical size carries the figure, and a heavy
   amber numeral would outweigh the page's h1. Lining and proportional, not
   tabular: tabular pads the single-digit 2 and 8 so they stop hugging the
   left edge the way 12 does (DESIGN_BRIEF 2.4). The figure and the label
   are spans set as blocks, not paragraphs: inside a link they are one
   phrase, and a large <p> over a smaller one reads as a heading to a
   checker (axe p-as-heading). */
.glance__fig{grid-area:1/1;display:block;margin:0;font:400 40px/1 var(--serif);
  letter-spacing:-.014em;color:var(--accent);
  font-variant-numeric:lining-nums proportional-nums}
.glance__n{display:block}
.glance__label{grid-area:1/2;display:flex;align-items:center;gap:4px;margin:0;
  font:600 19px/1.35 var(--serif);color:var(--ink)}
.glance__label span{text-decoration-line:underline;text-decoration-thickness:1px;
  text-underline-offset:4px;text-decoration-color:transparent;
  transition:text-decoration-color var(--t-quick) var(--ease-state)}
.glance__label svg{flex:none;display:block;overflow:visible;color:var(--muted);
  transition:color var(--t-quick) var(--ease-state)}
.glance__shaft{stroke-dasharray:13;stroke-dashoffset:5}
/* no font shorthand: it would reset the body's old-style figures */
.glance__note{grid-area:2/2;margin:4px 0 0;font-size:16px;line-height:1.5;
  color:var(--muted)}
@container glance (min-width:740px){
  .glance__card{grid-column:auto}
  .glance__a{display:block;height:100%;padding:24px 12px 16px}
  .glance__label{margin-top:12px}
  .glance__card:nth-child(2){--i:1}
  .glance__card:nth-child(3){--i:2}
}
@media (hover:hover){
  a.glance__a:hover::before{opacity:1;transform:none}
  a.glance__a:hover .glance__label span{text-decoration-color:currentColor}
  a.glance__a:hover .glance__label svg{color:var(--body)}
}
/* a press: the fill a step deeper, and the card gives a little under the
   finger (.98, the home page's rows), back on the quick spring */
a.glance__a:active::before{opacity:1;transform:none;background:var(--card);
  background:color-mix(in oklab,var(--ink) 7%,var(--page))}
.glance__a:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
@media (prefers-reduced-motion:no-preference){
  .glance__shaft{transition:stroke-dashoffset var(--spring-fast)}
  .glance__head{transition:transform var(--spring-fast)}
  a.glance__a{transition:transform var(--spring-quick)}
  a.glance__a:active{transform:scale(.98)}
}
/* Arriving is drawn, leaving is quick: the fill unrolls from the hairline
   on the mid spring and fades in 120ms as the pointer leaves; it is rolled
   back up only once it is gone, so a pointer that comes straight back finds
   it where it was. */
@media (hover:hover) and (prefers-reduced-motion:no-preference){
  .glance__a::before{transition:opacity var(--t-quick) var(--ease-state),
    transform 0s linear var(--t-quick)}
  a.glance__a:hover::before{transition:opacity 0s,transform var(--spring-mid)}
  a.glance__a:hover .glance__shaft{stroke-dashoffset:0;transition-duration:var(--t-mid)}
  a.glance__a:hover .glance__head{transform:translateX(5px);
    transition:transform var(--spring-mid) 60ms}
}
/* keyboard focus: the hover's end state at once, no travel for a key. As
   weighty as the hover rules and after them, so it wins where both apply. */
a.glance__a:focus-visible::before{opacity:1;transform:none;transition:none}
a.glance__a:focus-visible .glance__label span{text-decoration-color:currentColor;
  transition:none}
@media (prefers-reduced-motion:no-preference){
  a.glance__a:focus-visible .glance__shaft{stroke-dashoffset:0;transition:none}
  a.glance__a:focus-visible .glance__head{transform:translateX(5px);transition:none}
}
@media (prefers-reduced-motion:reduce){.glance__shaft{stroke-dashoffset:0}}
@media (forced-colors:active){
  .glance__label svg{color:LinkText}
  .glance__a::before{display:none}
}

/* The reveal, once, on the way down. Its start state exists only on screen,
   only without a reduced-motion request and only on a card the script marks
   .is-out, so print, a page without scripts and reduced motion never see it.
   The hairline draws left to right, then the figure comes up out of its own
   line box on the slow spring and settles, sharpening as it slows (a 2px
   blur at the start, gone by the time it lands), and the words follow.
   Three across, the cards cascade 70ms apart; as rows each arrives on its
   own. */
@media screen and (prefers-reduced-motion:no-preference){
  .glance__card.is-out::before{transform:scaleX(0)}
  .glance__card.is-out .glance__n{transform:translateY(100%)}
  .glance__card.is-out .glance__label,.glance__card.is-out .glance__note{
    opacity:0}
  /* clipped above only: sideways and below it leaves room for a wider
     figure and a falling old-style digit in the fallback face */
  .glance__card.is-out .glance__fig,.glance__card.is-in .glance__fig{
    clip-path:inset(0 -1em -.1em)}
  .glance__card.is-in::before{
    animation:glance-draw var(--spring-slow) calc(var(--i,0)*70ms) backwards}
  .glance__card.is-in .glance__n{
    animation:glance-rise var(--spring-slow) calc(var(--i,0)*70ms + 60ms) backwards,
      glance-focus var(--t-mid) var(--ease-state) calc(var(--i,0)*70ms + 60ms) backwards}
  .glance__card.is-in .glance__label,.glance__card.is-in .glance__note{
    animation:glance-fade var(--t-slow) var(--ease-state) calc(var(--i,0)*70ms + 140ms) backwards,
      glance-lift var(--spring-mid) calc(var(--i,0)*70ms + 140ms) backwards}
}
@keyframes glance-draw{from{transform:scaleX(0)}}
@keyframes glance-rise{from{transform:translateY(100%)}}
@keyframes glance-focus{from{filter:blur(2px)}}
@keyframes glance-fade{from{opacity:0}}
@keyframes glance-lift{from{transform:translateY(6px)}}

@media print{.glance__card{break-inside:avoid}}
"""

# A one-time reveal. The figures are visible by default and are hidden on the
# first scroll only if they were below the fold when the page opened, so a
# page nobody scrolls (a screenshot, a print, a preview, a frame sized to its
# content) never loses them, and a first scroll that lands on them still
# sees them arrive. Failsafe: a callback that reports no intersection changes
# nothing, whatever the observer does a hidden figure on screen is shown
# within a second, and a figure that takes keyboard focus is shown at once.
JS += """
(function(){
  var boot=function(){
    var cards=[].slice.call(document.querySelectorAll('.glance__card'));
    if(!cards.length||!('IntersectionObserver' in window)||!window.matchMedia||
      !matchMedia('screen and (prefers-reduced-motion: no-preference)').matches)return;
    var y0=scrollY;
    addEventListener('scroll',function(){
      if(cards[0].getBoundingClientRect().top+scrollY-y0<innerHeight)return;
      var out=cards.slice(),
        show=function(c){var i=out.indexOf(c);if(i<0)return;
          out.splice(i,1);io.unobserve(c);c.classList.replace('is-out','is-in')},
        io=new IntersectionObserver(function(es){es.forEach(function(e){
          if(e.isIntersecting)show(e.target)})},{rootMargin:'0px 0px -10% 0px'}),
        dog=setInterval(function(){out.slice().forEach(function(c){
          var r=c.getBoundingClientRect();if(r.top<innerHeight&&r.bottom>0)show(c)});
          if(!out.length)clearInterval(dog)},1000);
      cards.forEach(function(c){c.classList.add('is-out');io.observe(c);
        c.addEventListener('focusin',function(){show(c)})});
    },{once:true,passive:true});
  };
  if(document.readyState==='loading')addEventListener('DOMContentLoaded',boot);
  else boot();
})();
"""

# (figure, label, note, the CV section that lists them). The facts of his last
# About paragraph, in his words: "12 published articles; 2 patents, one
# granted and the other pending; and 8 awards received through academic and
# industry-academia collaborative research grants." The anchors are cv.json's
# section ids, which parts/cv.py gives its sections; build.py's link report
# fails a --strict build if one stops resolving.
FIGURES = (
    ("12", "Published articles", "", "journal-publications"),
    ("2", "Patents", "One granted and the other pending", "patents"),
    ("8", "Awards", "Received through academic and industry-academia "
                    "collaborative research grants", "awards"),
)

_GARROW = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" '
           'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
           'stroke-linejoin="round" aria-hidden="true">'
           '<path class="glance__shaft" d="M3.5 12h13"/>'
           '<path class="glance__head" d="m11.5 6.8 5.2 5.2-5.2 5.2"/></svg>')


def render_glance(cv_href=CV_HREF):
    """Return the 'At a glance' section as an HTML string. Each figure links
    to its section of the CV page at cv_href; a falsy cv_href drops the links."""
    cards = []
    for figure, label, note, anchor in FIGURES:
        inner = ('<span class="glance__fig"><span class="glance__n">%s</span></span> '
                 '<span class="glance__label"><span>%s</span>%s</span>%s'
                 % (figure, label, _GARROW if cv_href else "",
                    ' <p class="glance__note">%s</p>' % note if note else ""))
        if cv_href:
            inner = '<a class="glance__a" href="%s#%s">%s</a>' % (cv_href, anchor, inner)
        else:
            inner = '<div class="glance__a">%s</div>' % inner
        cards.append('<li class="glance__card">%s</li>' % inner)
    return (
        '<section class="glance" aria-labelledby="glance-title">'
        '<div class="glance__head">'
        '<h2 class="glance__title" id="glance-title">At a glance</h2>'
        '<p class="glance__when"><time datetime="2026-09">September 2026</time></p>'
        '</div>'
        '<ul class="glance__grid" role="list">%s</ul>'
        '</section>' % "".join(cards))


def render_timeline():
    """Return the career timeline, as parts/timeline.py renders it.

    If that module cannot be imported, return "".
    """
    try:
        from parts import timeline
    except ImportError:
        return ""
    return timeline.render()
