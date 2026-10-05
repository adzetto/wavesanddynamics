# -*- coding: utf-8 -*-
"""column: the Big Picture row, and the list of his topics that unfolds under it.

Round 5 (site/design/ROUND5_SPEC.md, ruling "Column") made the column's fourth
row, "Big Picture of Waves and Data Analytics", expandable. On 25 Sep 2026 the
professor took his six topic rows out of the column: clicking Big Picture
opens the list, so they need not stand in the column as well. The list is now
the only place the column names them. Its items are the topics of the Big
Picture page (parts/documents.py, CATEGORIES), in the page's order, so the
reader meets one order everywhere, each under its short name and each opening
the page its old row opened: his three guides themselves, his probability deck
and the page in preparation (build.py's nav_html() pairs them). His research
is not among them: it has a row of its own, My Research Areas.

Where it is open. On the Big Picture page, unless the reader has closed it.
On a page the list holds, a topic's own page or a document filed under a
topic (From Bridges to Photons, under Waves and Dynamics), it opens with the
page whatever the reader chose before, so the reader sees where they are: the
Big Picture row is lit as the section and the topic is marked. Elsewhere it
is as the reader last left it, closed at first.

The row keeps its link to big-picture.html and gains a button at its right
edge, as a macOS sidebar section does: the words go to the page, the chevron
shows what is in it.

The line (27 Sep 2026: the chevron draws the eye, the client wrote, and the
row itself could move the way a motion designer would make it). Under the
row's title stands the Big Picture page's own drawing in small: a hairline
through a bead for each topic, in the list's order, left to right as the page
sets them. Before anything opens it says what the row holds, topics in an
order and joined, the thing to grasp first. It is the list folded: the list
is the same line stood upright, as the page stands its own line upright on a
phone, so the topics are shown once, across the row or down the list, never
both. The list opens inside the column, under the row:

  - the line turns the corner: it runs off the row and down into the list
    at the fold's speed, each bead going out as the line's end passes it,
    while the branch comes down from where the line began, so the line
    across the row becomes the branch down the list;
  - the rows below move down and uncover the topics, which sit still in
    their places, so the column reads as one sheet folding open;
  - each topic fades in and drops the last 6px into place just after the
    edge has passed it, top to bottom, so the stagger is the fold itself;
  - the chevron, which points down at the list it will open, turns half
    round to point up, the way the list will fold back;
  - a white point rides the tip of the branch while it moves and is gone
    when it rests;
  - closing runs the same path back, and the line comes out along the row
    again.

The line keeps the column's states. Pointed at, its beads light as the row's
fill passes over them, left to right; a key lights them at once; pressed,
they go white with the row. On the Big Picture page, the row being the page,
they stand lit; on a topic's page folded shut, the topic's bead is warm,
where the list would mark it, so "you are here" travels with the topics and
is never shown twice either.

One number drives all of it: the fold's progress p, from 0 (closed) to 1
(open), on a critically damped spring (Apple's damping 1.0: no overshoot for
a menu), the site's own: the mid spring out and the fast one back (the
tokens of parts/springs.py, 240 and 160ms, 29 Sep 2026: the client asked
for all of it to be quicker), so the list opens a shade slower than it
goes away. A second click, or Escape, mid-way retargets the
spring from where it is and at the speed it has, so the motion turns round
without a seam. Only transform and opacity change while it moves: the list
is laid out once, and the rows below are translated up by what is still
folded, so no frame runs layout and nothing counts as a layout shift.

The call for a look (the professor, 25 Sep 2026, on a photo of the column:
the arrow could point down, and draw attention to that tab). Until the reader
has seen the list open once, a closed row asks for it: the chevron takes the
column's warm mark and, every 6s, dips twice and comes back while a warm ring
swells around the button and fades (the client, 27 Sep 2026: it draws the eye
nicely). It starts as the thought that runs the line when the page opens
lands in the chevron (the orbs, below); where no orb is drawn, once the row
is on screen and the page has been up 1.2s. The call rests while the row is
off screen or the tab is hidden. Asked for less motion, a warm dot stands on
the button instead. Seen open once (opened, or shown open by a page), it is
quiet for good.

Hover, where a pointer can hover and aim: the pointer resting on the row for
350ms opens the list, as the chevron would, and it stays open when the
pointer leaves. Hovering the row dips the chevron 2px the way it will go,
and the row fills as every row does (parts/theme.py), under its button too,
lighting the line's beads as the fill reaches them.
Pointing at a topic lights its way in from the row: the trunk down to its
bead, running on from topic to topic, the bead, its branch, then its words.
The topics take no fill (29 Sep 2026: the client found the fill that swept
under the pointer very bad, and asked for the list to answer a finger on a
phone as well): white passes along the words from the branch, left to
right (a white copy of them uncovered by its clip), while a hairline draws
under them with the white's edge, and the bead wakes as an orb as the
thought reaches it. A finger gets the same from
the moment it lands (:active, and .p, which the script sets), on the quick
spring, so it shows before the page it opens has come, and nothing holds
the link back; a key takes the whole path at once.

The orbs (29 Sep 2026: the client asked for the line's dots, its strokes and
the chevron to come alive as the page opens, as motion.dev's thinking
particles and the thinking-orbs page do, small spheres of dots that turn
beside a word, and for the list and its topics too). What moves says what
the row holds: five topics on one line, joined in the Big Picture's order,
and the list the chevron opens. One point, the thought, white in a soft
light of the column's own (warm is "you are here" and the chevron's alone:
the client disliked orange in motion), travels the line the way the page
reads it, and each topic wakes as the thought reaches it:

  - a bead wakes into an orb: 48 dots on a sphere 13px across (the bead is
    7), laid evenly (a Fibonacci lattice), turning about an axis tilted
    toward the reader, each dot lit and sized by how near it is. It grows
    out of the bead's ring on the fast spring, turns for a moment (0.12s),
    spins down and settles back into the ring on the draw spring, so the
    motion ends on the still line's own pixels, and the next bead is
    already thinking as one settles;
  - as the page opens (once a page view, when the row is first on screen:
    at once on a desktop, as the phone's drawer first opens), the thought
    runs the line from the first topic to the fifth in 0.56s and on into
    the chevron in 0.27s, which gives once as it lands, or on a first visit
    begins its call; the list open, it runs down the branch through the
    topics at 420px a second. It all reads in about 1.2s, where it took
    2.5s (29 Sep 2026: the client asked for it faster);
  - the list opening, it rides the tip of the branch as the branch draws
    down, and each topic wakes as the edge uncovers it, top to bottom;
  - a topic under the pointer or a finger: the path lights from the row's
    line down the branch, the thought at its tip, and the topic's orb
    wakes as it arrives, stays alive while the topic is pointed at, and
    settles when the pointer leaves; a key takes the path and the orb at
    once;
  - "you are here", the topic a page is filed under, wakes warm as the
    thought passes, round its warm bead, and settles like the rest: once
    the page is still, nothing in the column moves but the call.

The row tells it again when the reader rests the pointer on it with the list
open (closed, the list opens instead, and that is its story) or brings a key
to it, no sooner than 1.6s after the last time. The title does not shimmer:
the words lead, and a sheen across them would decorate, not explain. It is
drawn on one canvas over the <li>, with frames asked for only while
something moves, none while the column is off screen or the tab is hidden,
and nothing on it at rest. Asked for less motion, with colours forced, or
without a canvas, none of it exists and the row is as the stylesheet draws
it.

The halo (29 Sep 2026: the client asked for the orbs on his photo too). The
portrait at the head of the column becomes an orb for a moment on the first
page of a visit, as the column arrives (parts/theme.py, THE ARRIVAL): the
dots of a sphere a little larger than the photo stand round it as it
resolves out of its blur, the ones over his face or behind it never drawn,
so only a band round the rim shows; they turn, and gather into the pale
ring 3.5px out from the photo, where they fade: it rests as the clean
hairline it was, in about 0.9s. On a phone the bar's small portrait does the
same once a visit, closer and finer. Pointing at the block, or a key coming
to it, the ring breathes out a shallow shell that turns and settles back,
fainter, while the round-10 ring draws itself; not within 1.6s of the last
time. Its dots are --focus, the blue a ring takes on paper, where the
portrait sits (the column's navy begins under the name). The canvas exists
for the motion alone: made as it starts, taken away as it rests, with
frames only between, none in a hidden tab; none of it under reduced motion
or forced colours, or without a script.

Keyboard and screen reader: a real <button> with aria-expanded and
aria-controls; focus stays on it. Escape on the row or in the list folds it
and puts focus back on the button (and stops there: in the phone drawer a
second Escape closes the drawer). While the list folds away it is inert, so
Tab never lands in it. Under prefers-reduced-motion the list opens and closes
at once, and the line turns with it. Without JavaScript the list shows on the
pages that open it, the line on the others, and the button is hidden, so the
row is round 4's link. The line and the orbs are drawn, not said
(aria-hidden), and nothing is announced: the list is where a screen reader
hears the topics.

Interface for build.py:
  categories() -> [(id, label, pages)]   the topics, and the pages filed under each
  row(href, title, on, up, items, where="") -> str   the Big Picture <li>
  head_js(page_open) -> str   for a <script> in <head>, beside the fold's
  CSS, JS                     module strings, like every part
"""

import html
import math

from .springs import SPRINGS

__all__ = ["CSS", "JS", "row", "head_js", "categories", "notes"]

# His five topics, in the Big Picture page's order (the professor, 27 Sep
# 2026: the page sets them on one line in this order), as categories() gives
# them. They are defined once, in parts/documents.py as CATEGORIES; this copy
# is only used while that module does not have them.
FALLBACK = (
    ("probability-statistics", "Probability & Statistics", ("probability-statistics.html",)),
    ("signal-processing", "Signal Processing & System ID",
     ("doc/signal-processing-system-identification-and-optimization.html",)),
    ("machine-learning", "Machine Learning",
     ("doc/machine-learning-the-complete-picture-and-guide-5.html",)),
    ("waves-dynamics", "Waves and Dynamics",
     ("doc/dynamical-behavior-of-engineering-structures-and-acoustic-wave-propagation.html",
      "doc/from-bridges-to-photons.html")),
    ("python-programming", "Python / Programming", ("python-programming.html",)),
)

# His research is on the page (all five topics serve it) but it is not a topic
# of the list: the column has its row, My Research Areas.
NOT_TOPICS = frozenset(("research",))


def categories():
    """(id, label, pages) for each topic, from parts/documents.py when it has
    them, in its order: the short label where there is one, and the pages
    filed under the topic, its page in preparation, its documents or its
    decks, in their order. His research, should the page file it with the
    topics, stays out (NOT_TOPICS). A topic with no page to open means that
    module is not in the shape this reads (it is written by hand), so the
    copy here stands in whole."""
    try:
        from parts.documents import CATEGORIES
        out = [(c["id"], c.get("short") or c["label"],
                tuple(([c["soon"]] if c.get("soon") else [])
                      + [f"doc/{d}.html" for d in c.get("docs") or ()]
                      + list(c.get("decks") or ())))
               for c in CATEGORIES if c["id"] not in NOT_TOPICS]
    except (ImportError, AttributeError, KeyError, TypeError):
        return list(FALLBACK)
    return out if out and all(pages for _, _, pages in out) else list(FALLBACK)


def notes():
    """{short label: note} for the topics that carry a line in smaller type
    under their name in the list (parts/documents.py, `note`): the signal
    processing guide's "(with connections to estimation, optimization, ML,
    inverse problems, BSS)", the professor's words (5 Oct 2026)."""
    try:
        from parts.documents import CATEGORIES
        return {c.get("short") or c["label"]: c["note"] for c in CATEGORIES if c.get("note")}
    except (ImportError, AttributeError, KeyError, TypeError):
        return {}


def _label(text, attr=False):
    # "Python / Programming" keeps "Python /" on one line, as the Big Picture
    # page sets it; the words' white copy (data-w) breaks where they do
    return html.escape(text, quote=attr).replace(" / ", "\u00a0/ ")


# The chevron: two, one over the other, the lower a step fainter, as a
# scroll cue draws them, and at stroke 2.2 where the inline family draws
# 1.5 (the professor, 26 Sep 2026: "daha belirgin, biraz daha thick ya da
# double arrow"). The pair is centred on the grid, so a half turn about the
# centre makes the "up" of an open list without moving it. It sits in a
# span (.nav__cv) that the call for a look and the thought's arrival nudge:
# a box of the page's own moves on the compositor, where the <svg> itself
# was restyled on every frame of the 6s loop (measured: 301 style
# recalculations in 5s, 52 through the span).
CHEVRON = ('<span class="nav__cv"><svg class="nav__chev" viewBox="0 0 24 24" width="22" height="22" '
           'fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
           'stroke-linejoin="round" aria-hidden="true" focusable="false">'
           '<path d="M7 6.5 12 11.5l5-5"/><path d="M7 12.5 12 17.5l5-5" opacity=".55"/></svg></span>')

# The line under the row's title: a bead for each topic, a stroke between
# neighbours, and the branch's first stretch, under the first bead (v), all
# empty <i>s that the stylesheet draws and the fold's script turns; --i is
# each one's place on the line. The bead of the topic the page is filed
# under is marked (h), warm where the list would be.
def _line(items):
    beads = "".join(f'<i class="b{" h" if it[2] else ""}" style="--i:{k}"></i>'
                    for k, it in enumerate(items))
    strokes = "".join(f'<i class="s" style="--i:{k}"></i>' for k in range(len(items) - 1))
    return f'<span class="nav__map" aria-hidden="true">{beads}{strokes}<i class="v"></i></span>'


# A page the list holds opens it before its first paint whatever the reader
# chose on another page. head_js() cannot tell such a page from the rest (it
# knows the Big Picture page alone), so the row carries the line itself, first
# in its <li>: it runs before the parser reaches the chevron and the list, and
# nothing above it in the page depends on it.
HOLD = '<script>document.documentElement.setAttribute("data-bp","open")</script>'


def row(href, title, on, up, items, where=""):
    """The Big Picture row, as build.py's nav_html() writes it.

    `on` is the attribute string nav_html() computes for the row's link
    (' class="on" aria-current="page"' on the Big Picture page, "true" on a
    page the list holds). `items` are the list's topics in their order,
    (label, href, current) each, or (label, href, current, note) for a topic
    with a line in smaller type under its name (notes()): `current` is
    "page" on the topic's own page, "true" on a document filed under it,
    else "". The line under the title
    draws a bead for each, in the same order. `where` is "here" on the
    Big Picture page and "in" on a page the list holds, the pages that show
    the list open when they load. The button's name is its title, the site's
    convention for an icon button (a matching aria-label made Chrome read it
    twice); the list carries the same name, so a screen reader that enters it
    hears where it is."""
    def topic(label, page, current, note=""):
        # a note goes under the words, inside the link, so the link's name
        # is everything it shows (WCAG 2.5.3); its row grows by the note and
        # keeps its bead and branch on the words' line (.nav__two)
        return (f'<li{" class=\"nav__two\"" if note else ""}><a href="{up}{page}"'
                + (f' aria-current="{current}"' if current else "")
                + f'><span class="nav__w" data-w="{_label(label, True)}">{_label(label)}</span>'
                + (f'<span class="nav__sep"> </span><span class="nav__n">{html.escape(note)}</span>'
                   if note else "")
                + '</a></li>')

    topics = "".join(topic(*it) for it in items)
    return (f'<li class="grp nav__bp{f" nav__bp--{where}" if where else ""}">'
            f'{HOLD if where == "in" else ""}'
            f'<div class="nav__row"><a href="{up}{href}"{on}><span class="nav__t">{title}</span>'
            f'{_line(items) if items else ""}</a>'
            f'<button class="nav__x" type="button" aria-expanded="{"true" if where else "false"}" '
            f'aria-controls="nav-bp" title="Big Picture topics">{CHEVRON}</button></div>'
            f'<div class="nav__fold" id="nav-bp"><ul class="nav__sub" aria-label="Big Picture topics">'
            f'{topics}</ul><i class="nav__tip" aria-hidden="true"></i></div></li>')


def head_js(page_open):
    """The state of the list before the first paint, beside the fold's script.

    It puts data-bp="open" or "closed" on <html>: the reader's own choice when
    there is one (localStorage "wad:bp"), else the page's default: open on
    the Big Picture page, closed elsewhere. (A page the list holds opens it
    all the same, by a line of its own: HOLD.) Storage may refuse (a private
    window): each call is in try/catch and the default applies.

    The arrival: a reader who has made no choice and comes to the Big
    Picture page from a page where the list was folded sees the first paint
    as they left it, folded, and then the list unfolds (data-bp-go, played
    by JS). "wad:bp-shown" in sessionStorage is what the last page showed.
    It plays once a visit ("wad:bp-arrived"): the first time it shows where
    the list lives; after that the list is simply open there.
    Leaving the Big Picture page does not play the fold back: the reader is
    looking at the new page, not at the column, and a motion nobody asked
    for in the corner of the eye would only pull it away.

    The call for a look: data-bp-new, while the reader has never seen the list
    open ("wad:bp-seen" is missing), which the stylesheet draws only on a
    closed list. The Big Picture page never asks, the list being its own; nor
    does a browser whose storage refuses, since it could not remember that
    the reader had answered, and would ask on every page.

    The column's arrival (parts/theme.py, THE ARRIVAL): data-id-in on the
    first page of a visit ("wad:id-in" in sessionStorage is missing), where
    the column stands open beside the page (above 1000px, not folded: the
    fold's script, which runs first, has set data-side) and motion is
    welcome. Once a visit: the column is the site's frame and every later
    page opens with it still. A browser whose storage refuses never gets it,
    since it could not remember that it had played."""
    return ('(function(h,D){var s,n,l,a,t,f;'
            'try{s=localStorage.getItem("wad:bp");n=localStorage.getItem("wad:bp-seen")}'
            'catch(e){n=1}'
            'try{l=sessionStorage.getItem("wad:bp-shown");a=sessionStorage.getItem("wad:bp-arrived")}'
            'catch(e){}'
            't=s==="open"||s==="closed"?s:D;f=t;'
            'if(t!==s&&t==="open"&&l==="closed"&&!a)f="closed";'
            'try{if(matchMedia("(prefers-reduced-motion: reduce)").matches)f=t}catch(e){}'
            'h.setAttribute("data-bp",f);if(f!==t)h.setAttribute("data-bp-go",t);'
            'if(!n&&D==="closed")h.setAttribute("data-bp-new","")'
            f'}})(document.documentElement,"{"open" if page_open else "closed"}");'
            '(function(h){try{if(h.getAttribute("data-side")!=="closed"'
            '&&matchMedia("(width > 1000px)").matches'
            '&&!matchMedia("(prefers-reduced-motion: reduce)").matches'
            '&&!sessionStorage.getItem("wad:id-in")){'
            'sessionStorage.setItem("wad:id-in","1");h.setAttribute("data-id-in","")}}'
            'catch(e){}})(document.documentElement);')


CSS = """
/* ==========================================================================
   THE BIG PICTURE ROW, and the list of his topics that unfolds under it
   The row is its link and a 40px button at its right edge (48px under a
   finger). The link's words wrap in 176px: "Big Picture of Waves" is 130px
   and "and Data Analytics" 119px in Source Sans 3 600 at 15px (measured in
   Chromium), so the title keeps its two lines. The button lights as part of
   the row when the link is hovered or current, and on its own hover shows a
   32px chip, so it reads as a control of its own. Without JavaScript
   (html has no data-bp) the button is hidden and the link takes the row.
   ========================================================================== */
.nav__bp{--bp-line:color-mix(in oklab,var(--nav-ink) 30%,var(--nav))}
.nav__row{display:flex;align-items:stretch}
.nav__row>a{flex:1 1 auto;min-width:0}
[data-bp] .nav__row>a{padding-right:4px}
.nav__x{position:relative;flex:none;display:none;place-items:center;width:40px;margin:0;
  padding:0;border:0;border-radius:0;background:transparent;color:var(--nav-mute);
  font:inherit;cursor:pointer;-webkit-tap-highlight-color:transparent;
  transition:background-color var(--t-quick) var(--ease-state),color var(--t-quick) var(--ease-state)}
[data-bp] .nav__x{display:grid}
@media (pointer:coarse){.nav__x{width:48px}}
.nav__x::before{content:"";position:absolute;left:4px;right:4px;top:50%;height:32px;
  margin-top:-16px;border-radius:var(--r-sm);
  transition:background-color var(--t-quick) var(--ease-state)}
/* the chevron points down at the closed list and up at the open one; the
   script turns it between the two on the fold's spring */
.nav__cv,.nav__chev{position:relative;display:block}
[data-bp="open"] .nav__chev{transform:rotate(-180deg)}
/* the call for a look takes the column's warm mark (4.90:1); :where() keeps
   it under the hover and focus states below, which take the chevron white */
:where([data-bp-new][data-bp="closed"]) .nav__x{color:var(--accent-on-nav)}
/* the group's hairline, on both halves of the row */
.nav .grp>.nav__row>a,.nav .grp>.nav__row>.nav__x{box-shadow:inset 0 1px 0 var(--nav-rule)}
/* the row fills as one: the link's fill (parts/theme.py, the rows' states)
   runs on under the button to the column's edge, so the wipe crosses the
   whole row; the button only turns its chevron white */
[data-bp] .nav__row>a::after{right:-40px}
@media (pointer:coarse){[data-bp] .nav__row>a::after{right:-48px}}
@media (hover:hover){
  .nav__row>a:hover+.nav__x{color:var(--nav-ink)}
  .nav__x:hover{color:var(--nav-ink)}
  .nav__x:hover::before{background:var(--nav-hover)}
  .nav__row>a.on+.nav__x:hover::before{
    background:color-mix(in oklab,var(--nav-ink) 10%,var(--nav-hover))}
}
.nav__row>a.on+.nav__x{background:var(--nav-hover)}
.nav__row>a:active+.nav__x{background:var(--nav-press)}
.nav__x:active::before{background:var(--nav-press)}
.nav__x:focus-visible{outline:2px solid var(--nav-ink);outline-offset:-4px;color:var(--nav-ink)}
/* Hovering the row, the chevron gives 2px the way it points: down at the
   list it would open, up once it is open. It is the path that moves, inside
   the turning icon, so the dip turns with it and never meets the nudge
   below, which moves the icon itself (1 unit of the grid is 0.83px). */
@media (hover:hover) and (pointer:fine) and (prefers-reduced-motion:no-preference){
  .nav__chev path{transition:translate var(--spring-fast)}
  .nav__row:hover .nav__chev path{translate:0 2.4px}
}

/* THE LINE under the row's title (the module's docstring): the Big Picture
   page's line in small, a 7px ring for each topic, 28px apart, and a 1px
   stroke between neighbours that meets each ring, as the page's line meets
   its nodes. The rings are the list's beads, which they become, and the
   first one's centre is at x=20.5, over the list's branch, so the line turns
   into the branch on one axis. 7px under the title (the rows' 2px gap and
   5px), 119px long for five topics, the width of "and Data Analytics". At
   rest, white at 45% on the navy: under the words, which lead, and clearer
   than the list's 30% hairline, since here it stands alone. Its states are
   colour only, and the fold's script moves it by transform and opacity. */
.nav__map{--gap:28px;--map:color-mix(in oklab,var(--nav-ink) 45%,var(--nav));
  position:relative;display:block;flex:none;width:0;height:7px;margin:5px 0 0 -3px;
  pointer-events:none}
.nav__map i{position:absolute;display:block;left:calc(var(--i) * var(--gap))}
.nav__map .b{top:0;width:7px;height:7px;box-sizing:border-box;border:1px solid var(--map);
  border-radius:50%;transition:background-color var(--t-quick) var(--ease-state),
    border-color var(--t-quick) var(--ease-state)}
.nav__map .s{top:3px;width:calc(var(--gap) - 7px);height:1px;margin-left:7px;background:var(--map);
  transform-origin:0 50%;transition:background-color var(--t-quick) var(--ease-state)}
/* the branch's first stretch, from the first bead's centre down to the
   row's foot (its bottom padding, --pad and 1px), where the list's own
   branch goes on */
.nav__map .v{left:3px;top:3px;width:1px;height:calc(var(--pad) + 5px);background:var(--bp-line);
  transform:scaleY(0);transform-origin:50% 0}
/* open, the line has turned down into the list: the beads and strokes are
   gone and the branch's first stretch stands. Without the script, so on
   the pages whose list shows. */
:is(.nav__bp--here,.nav__bp--in) .nav__map :is(.b,.s),[data-bp="open"] .nav__map :is(.b,.s){opacity:0}
:is(.nav__bp--here,.nav__bp--in) .nav__map .v,[data-bp="open"] .nav__map .v{transform:none}
[data-bp="closed"] .nav__map :is(.b,.s){opacity:1}
[data-bp="closed"] .nav__map .v{transform:scaleY(0)}
/* lit, as the list lights a topic's bead: the row being the page (the Big
   Picture page's, a topic's), under the pointer, or under a key. Under the
   pointer each bead lights as the row's fill reaches it, which the mid
   spring carries across the row's 240px in 90ms: the beads at 20.5 to
   132.5px are passed 18 to 86ms in. Leaving, they go out together. */
:where(.nav__row>a.on) .nav__map .b{background:var(--nav-mute);border-color:var(--nav-mute)}
:where(.nav__row>a.on) .nav__map .s{background:var(--nav-mute)}
@media (hover:hover){
  :where(.nav__row:hover) .nav__map .b{background:var(--nav-mute);border-color:var(--nav-mute);
    transition-delay:calc(18ms + var(--i) * 17ms)}
  :where(.nav__row:hover) .nav__map .s{background:var(--nav-mute);
    transition-delay:calc(27ms + var(--i) * 17ms)}
}
:where(.nav__row:has(:focus-visible)) .nav__map .b{background:var(--nav-mute);
  border-color:var(--nav-mute);transition:none}
:where(.nav__row:has(:focus-visible)) .nav__map .s{background:var(--nav-mute);transition:none}
/* pressed, the row one step deeper and its line white */
:where(.nav__row>a:active) .nav__map .b{background:var(--nav-ink);border-color:var(--nav-ink)}
:where(.nav__row>a:active) .nav__map .s{background:var(--nav-ink)}
/* on a topic's page, the list folded, the topic's bead takes the warm of
   "you are here" (4.90:1), where the list would mark it */
.nav__row>a.on .nav__map .b.h{background:var(--accent-on-nav);border-color:var(--accent-on-nav)}

/* The call for a look. The professor asked for the row to draw the eye
   (25 Sep 2026), and nothing on it said that it opens. Until the reader has
   seen the list open once (head_js() marks <html> data-bp-new), a closed
   list asks. The script marks the row .nav__bp--call as the thought that
   runs the line when the page opens lands in the chevron (THE ORBS; where
   none is drawn, once the row is on screen and the page has been up
   1.2s): from then, every 6s, the chevron dips 3px and then 2px, two beats
   that come back on the site's firm ease-out and settle without overshoot
   (a serious site does not bounce, ROUND10), and a warm ring swells from
   under it and fades, once a nudge. While the row is off screen or the
   tab is hidden the script marks it .nav__bp--still and the call rests
   where it is. The ring grows to about 36px of the 40px button
   and its glow is 4px: the button is flush with the column's right edge,
   where .nav clips, and a ring grown past 1.29 had its edge and its glow
   cut flat there. The nudge is the translate of the chevron's span, which
   the fold's rotation (the icon's transform, written by the script)
   composes with and never replaces; the ring is the button's ::after,
   transform and opacity only, so none of it lays anything out, and both
   run on the compositor. Asked for less motion, nothing moves: a warm dot
   stands on the button. */
.nav__x::after{content:"";position:absolute;border-radius:50%;opacity:0;pointer-events:none}
@media (prefers-reduced-motion:no-preference){
  .nav__x::after{left:50%;top:50%;width:28px;height:28px;margin:-14px 0 0 -14px;
    box-shadow:0 0 0 1.5px color-mix(in oklab,var(--accent-on-nav) 75%,transparent),
      0 0 4px 0 color-mix(in oklab,var(--accent-on-nav) 40%,transparent)}
  :where([data-bp-new][data-bp="closed"]) .nav__bp--call .nav__cv{
    animation:bpnav-nudge 6s cubic-bezier(.3,0,.2,1) infinite}
  :where([data-bp-new][data-bp="closed"]) .nav__bp--call .nav__x::after{
    animation:bpnav-ring 6s cubic-bezier(.2,.8,.2,1) infinite}
  .nav__bp.nav__bp--still .nav__cv,.nav__bp.nav__bp--still .nav__x::after{
    animation-play-state:paused}
}
/* 1% of the loop is 60ms: down in 150ms, back in 300ms,
   the second beat the same at two thirds the depth; then five seconds still */
@keyframes bpnav-nudge{
  0%{translate:0 0}
  2.5%{translate:0 3px;animation-timing-function:cubic-bezier(.2,.8,.2,1)}
  7.5%{translate:0 0}
  9.5%{translate:0 2px;animation-timing-function:cubic-bezier(.2,.8,.2,1)}
  14.5%,100%{translate:0 0}
}
@keyframes bpnav-ring{
  0%{opacity:0;transform:scale(.55)}
  4%{opacity:.7;animation-timing-function:cubic-bezier(.4,0,.6,1)}
  24%,100%{opacity:0;transform:scale(1.15)}
}
/* the dot sits off the chevron's upper right arm, 2px clear of its stroke */
@media (prefers-reduced-motion:reduce){
  [data-bp-new][data-bp="closed"] .nav__x::after{left:calc(50% + 5.5px);top:calc(50% - 8.5px);
    width:5px;height:5px;background:var(--accent-on-nav);opacity:1}
}

/* The fold: the window the topics are uncovered through. It is laid out
   once, open, and the script moves it with the rows below while the list
   inside is held still, so the window's lower edge slides down the list.
   It takes no pointer; the list inside does. Without the script it shows
   on the pages that open it, the Big Picture page and the pages it holds. */
.nav__fold{display:none;position:relative;overflow:hidden;pointer-events:none}
.nav__bp--here .nav__fold,.nav__bp--in .nav__fold,[data-bp="open"] .nav__fold{display:block}
[data-bp="closed"] .nav__fold{display:none}
.nav__sub{position:relative;isolation:isolate;list-style:none;margin:0;padding:2px 0 12px;
  pointer-events:auto;--u:32}
/* the trunk, from under the row's title to the last topic's bead; over a
   lit topic's fill, under the beads */
.nav__sub::before{content:"";position:absolute;z-index:1;left:20px;top:0;bottom:28px;width:1px;
  background:var(--bp-line)}
.nav .nav__sub li{margin:0;position:relative}
/* a short branch from the trunk to each topic */
.nav .nav__sub li::after{content:"";position:absolute;left:24px;top:50%;width:8px;height:1px;
  background:var(--bp-line);pointer-events:none}
.nav .nav__sub li:has(a[aria-current])::after{background:var(--accent-on-nav)}
/* A topic: the sans at 400 / 14px in --nav-mute (8.40:1 on the column),
   white when current, 16px in from the rows' edge, one line each (the
   longest, "Signal Processing & System ID", is 178px of the 188 it has,
   183px set at 600 on its guide's page). 32px tall, 44px under a finger.
   It takes neither the rows' fill nor their press shade (the client, 29
   Sep 2026: the fill that swept under the pointer was very bad): a topic
   lights by its line, its bead, and its words. */
.nav .nav__sub a{min-height:32px;padding:6px 16px 6px 36px;gap:0;
  font:400 14px/1.3 var(--sans);letter-spacing:.01em;color:var(--nav-mute)}
.nav .nav__sub a::after{content:none}
.nav .nav__sub a:active{background:transparent}
/* its bead on the trunk, in place of the rows' rail */
.nav .nav__sub a::before{z-index:2;left:17px;top:50%;bottom:auto;width:7px;height:7px;margin-top:-3.5px;box-sizing:border-box;
  border:1px solid var(--bp-line);border-radius:50%;background:var(--nav);opacity:1;transform:none;
  transition:transform var(--spring-fast),background-color var(--t-quick) var(--ease-state),
    border-color var(--t-quick) var(--ease-state)}
@media (pointer:coarse){
  .nav__sub{--u:44}
  .nav .nav__sub a{min-height:44px}
  .nav__sub::before{bottom:34px}
}
/* A topic's note (notes()): under its words, in the sans at 12px in the
   topics' grey, three lines kept (the signal processing guide's runs to
   three in the column's 188px), so the row is one row and a set height
   taller wherever it is drawn. Its bead and branch stay on the words' line,
   half a row down, and the trunk lights that much further for the topics
   below it (--x, in px as --u is). */
.nav .nav__sub .nav__n{display:block;max-width:100%;height:3.9em;margin-top:1px;overflow:hidden;
  font:400 12px/1.3 var(--sans);letter-spacing:.01em;color:var(--nav-mute);opacity:.88;
  text-wrap:pretty}
.nav .nav__sub a[aria-current] .nav__n{color:var(--nav-ink);opacity:.8}
.nav .nav__sub li.nav__two>a{justify-content:flex-start}
.nav .nav__sub li.nav__two>a::before,
.nav .nav__sub li.nav__two::after,
.nav .nav__sub li.nav__two::before{top:calc(var(--u) * .5px)}
.nav__sub:has(>li.nav__two ~ li>a:is(:focus-visible,:active,.p)){--x:48}

/* Pointing at a topic lights its way in from the Big Picture row, a path
   through the tree drawn in one gesture of about 0.3s, with no block of
   colour anywhere in it:
   - the trunk lights from under the row's title down to the topic's bead
     (the list's ::after, scaleY from the top on the mid spring; with the
     orbs, the thought runs down it on the canvas); moving on to the next
     topic, it runs on from where it is, a row further or back, and it
     goes out, fading, when the pointer leaves the list;
   - the bead fills and swells a little (x1.3 on the fast spring), or
     wakes as an orb as the thought reaches it;
   - the topic's branch lights from the trunk to its words (its item's
     ::before, scaleX on the fast spring, 60ms behind);
   - then its words, as the thought arrives (90ms behind): white passes
     along them from the branch, left to right, and a hairline draws under
     them with the light's edge, both on the mid spring (THE WORDS, below).
   The light is --nav-mute and white, the column's own; warm stays with the
   current topic, which has its warm bead and branch and takes none of
   this. Where the trunk stops is where the topic's bead is: 2px of the
   list's padding, half a row, then a row per topic above it (32px rows,
   44px under a finger), as a share of a line 12 rows long, so the line
   only ever shrinks. Each topic's place in the list (--k) comes from
   :has(); a browser without it lights all but the trunk. A key takes the
   whole path at once, and a finger on the quick spring from the press
   (:active, or .p, which the script sets as the finger lands), so it
   shows before the page it opens has come. Leaving fades each piece
   where it stands, and folds it back unseen. */
.nav .nav__sub li::before{content:"";position:absolute;left:24px;top:50%;width:8px;height:1px;
  background:var(--nav-mute);pointer-events:none;opacity:0;transform:scaleX(0);transform-origin:0 50%;
  transition:opacity var(--t-quick) var(--ease-state),transform 0s var(--t-quick)}
.nav__sub::after{content:"";position:absolute;z-index:1;left:20px;top:0;width:1px;
  height:calc(var(--u) * 12px);background:var(--nav-mute);pointer-events:none;
  opacity:0;transform:scaleY(0);transform-origin:50% 0;
  transition:opacity var(--t-quick) var(--ease-state),transform 0s var(--t-quick);
  --reach:calc((var(--k) * var(--u) - var(--u) / 2 + 2 + var(--x, 0)) / (var(--u) * 12))}
.nav .nav__sub li:has(>a[aria-current])::before{content:none}   /* alone: :has() is unforgiving */
/* THE WORDS. A topic's words are their own grey, and a white copy of them
   (the span's data-w, drawn and not said: its alternative text is empty)
   lies over them, uncovered from the left by its clip, which travels on a
   spring, and faded where it stands when the pointer leaves. Under them a
   hairline, 5px under the baseline and clear of the descenders, draws from
   the left with the white's edge. A browser that cannot hide the copy from
   a screen reader draws neither copy nor light: the hairline says it. */
.nav .nav__sub a:not([aria-current]) .nav__w{position:relative;display:block;max-width:100%}
.nav .nav__sub a:not([aria-current]) .nav__w::before{content:attr(data-w) / "";position:absolute;inset:0;
  color:var(--nav-ink);pointer-events:none;opacity:0;clip-path:inset(0 100% 0 0);
  transition:opacity var(--t-quick) var(--ease-state),clip-path 0s var(--t-quick)}
.nav .nav__sub a:not([aria-current]) .nav__w::after{content:"";position:absolute;left:0;right:0;
  bottom:-2px;height:1px;background:var(--nav-mute);pointer-events:none;
  opacity:0;transform:scaleX(0);transform-origin:0 50%;
  transition:opacity var(--t-quick) var(--ease-state),transform 0s var(--t-quick)}
@media (hover:hover){
  .nav .nav__sub a:not([aria-current]):hover::before{border-color:var(--nav-mute);
    background:var(--nav-mute);transform:scale(1.3)}
  .nav .nav__sub li:hover::before{opacity:1;transform:none;transition:transform var(--spring-fast) 60ms}
  .nav__sub:has(>li>a:not([aria-current]):hover)::after{opacity:1;transform:scaleY(var(--reach));
    transition:transform var(--spring-mid)}
  .nav .nav__sub a:not([aria-current]):hover .nav__w::before{opacity:1;clip-path:inset(0);
    transition:clip-path var(--spring-mid) 90ms}
  .nav .nav__sub a:not([aria-current]):hover .nav__w::after{opacity:1;transform:none;
    transition:transform var(--spring-mid) 90ms}
/*K:hover*/
  .nav__sub:has(>li.nav__two ~ li>a:hover){--x:48}
}
/* a finger, from the press */
.nav .nav__sub a:not([aria-current]):is(:active,.p)::before{border-color:var(--nav-mute);
  background:var(--nav-mute);transform:scale(1.3)}
.nav .nav__sub li:has(>a:not([aria-current]):is(:active,.p))::before{opacity:1;transform:none;
  transition:transform var(--spring-quick)}
.nav .nav__sub a:not([aria-current]):is(:active,.p) .nav__w::before{opacity:1;clip-path:inset(0);
  transition:clip-path var(--spring-quick)}
.nav .nav__sub a:not([aria-current]):is(:active,.p) .nav__w::after{opacity:1;transform:none;
  transition:transform var(--spring-quick)}
.nav__sub:has(>li>a:not([aria-current]):is(:active,.p))::after{opacity:1;transform:scaleY(var(--reach));
  transition:transform var(--spring-quick)}
/*K:press*/
/* a key, at once */
.nav .nav__sub a:not([aria-current]):focus-visible::before{border-color:var(--nav-mute);
  background:var(--nav-mute);transform:scale(1.3);transition:none}
.nav .nav__sub li:has(>a:focus-visible)::before{opacity:1;transform:none;transition:none}
.nav__sub:has(>li>a:not([aria-current]):focus-visible)::after{opacity:1;
  transform:scaleY(var(--reach));transition:none}
.nav .nav__sub a:not([aria-current]):focus-visible .nav__w::before{opacity:1;clip-path:inset(0);
  transition:none}
.nav .nav__sub a:not([aria-current]):focus-visible .nav__w::after{opacity:1;transform:none;
  transition:none}
/*K:focus-visible*/
/* the topic of the page the reader is on (aria-current "page"), or the one a
   document is filed under ("true"): its bead takes the column's warm mark
   (4.90:1), its name goes white and 600 */
.nav .nav__sub a[aria-current]{color:var(--nav-ink);font-weight:600}
.nav .nav__sub a[aria-current]::before{border-color:var(--accent-on-nav);
  background:var(--accent-on-nav)}
/* the point at the tip of the branch, white in the column's light (warm is
   "you are here" and the chevron's alone): it sits on the window's lower
   edge, so it travels with the fold; the script lights it by the fold's
   speed, so it shows only while the branch is drawing */
.nav__tip{position:absolute;left:18px;bottom:1px;width:5px;height:5px;border-radius:50%;
  background:var(--nav-ink);opacity:0;pointer-events:none;
  box-shadow:0 0 0 3px color-mix(in oklab,var(--nav-mute) 30%,transparent)}

/* THE ORBS (the module's docstring). The script draws them on one canvas
   laid over the row and its list, which takes no pointer and is only there
   where motion is welcome and colours are not forced. While a bead is an
   orb its ring gives way (.o: its colours go, in --t-quick, while the dots
   grow out of it) and comes back as the orb settles into it. A topic under
   the pointer, a finger or a key keeps its ring still: the orb is its lit
   state, and the canvas draws the lit path down the branch, from the row's
   line, with the thought at its tip; the point at the tip of a moving fold
   is the canvas's too. */
.nav__bp--orbs{position:relative}
.nav__orbs{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none}
.nav__bp--orbs .nav__tip,.nav__bp--orbs .nav__sub::after{display:none}
.nav__map .b.o{border-color:transparent;background-color:transparent}
.nav .nav__bp.nav__bp--orbs .nav__sub a:not([aria-current])::before{
  border-color:var(--bp-line);background-color:var(--nav);transform:none}
.nav .nav__bp.nav__bp--orbs .nav__sub a.o:not([aria-current])::before{
  border-color:transparent;background-color:transparent}

/* A longer column scrolls sooner. Its foot says so: a 24px fade into the
   navy at the bottom of the scrolling list while more of it is below
   (.nav--more, kept by the script), gone at the end. Scrolling to a focused
   row stops clear of it, and the list never re-anchors its scroll when the
   fold opens above what is on screen.
   The fade replaces the desktop list's thin scrollbar. A classic scrollbar
   (Windows) takes 10px of the column's width while it shows, so opening the
   list in a window too short for it pulled every row's right edge and the
   button under the pointer 10px left, and closing pushed them back.
   A stable gutter would stop the jump but would end every lit row 10px
   short of the column's edge on every page. The phone drawer's scrollbar
   is an overlay and stays. */
.nav,.side{overflow-anchor:none}
@media (width > 1000px){
  [data-side] .nav{scrollbar-width:none}
  [data-side] .nav::-webkit-scrollbar{display:none}
}
.nav::after{content:"";position:sticky;bottom:0;display:block;height:24px;margin-top:-24px;
  background:linear-gradient(to bottom,transparent,var(--nav));opacity:0;pointer-events:none;
  transition:opacity var(--t-fast) var(--ease-state)}
.nav.nav--more::after{opacity:1}
.nav,.side{scroll-padding-bottom:24px}

@media (forced-colors:active){
  .nav__x{border:1px solid ButtonBorder}
  .nav__sub::before{background:CanvasText}
  .nav .nav__sub a::before{border-color:CanvasText;background:Canvas}
  .nav .nav__sub a[aria-current]::before{border-color:Highlight;background:Highlight}
  .nav__map .b{border-color:CanvasText;background:Canvas}
  .nav__map :is(.s,.v){background:CanvasText}
  .nav__row>a.on .nav__map .b.h{border-color:Highlight;background:Highlight}
  .nav .nav__sub a .nav__w::before{content:none}
  .nav .nav__sub a .nav__w::after{background:CanvasText}
  .nav__tip,.nav::after,.nav__x::after,.nav__sub::after,.nav .nav__sub li::before,
  .nav__orbs{display:none}
}
"""

# Each topic's place in the list (--k), for how far the trunk lights: ten
# places, twice the five the list holds today.
CSS = CSS.replace("/*K:hover*/\n", "".join(
    f"  .nav__sub:has(>li:nth-child({k})>a:hover){{--k:{k}}}\n" for k in range(1, 11)))
CSS = CSS.replace("/*K:focus-visible*/\n", "".join(
    f".nav__sub:has(>li:nth-child({k})>a:focus-visible){{--k:{k}}}\n" for k in range(1, 11)))
CSS = CSS.replace("/*K:press*/\n", "".join(
    f".nav__sub:has(>li:nth-child({k})>a:is(:active,.p)){{--k:{k}}}\n" for k in range(1, 11)))

JS = r"""
/* The site's springs (parts/springs.py), as the rate w of a critically
   damped spring, which the script integrates exactly: Motion's spring() of
   the token's visual duration v, bounce 0, is w = 2 pi / 1.2v. */
var SPR=/*SPR*/;
/* The column's arrival (parts/theme.py, THE ARRIVAL) has played: its mark
   leaves once the last of its animations is over, so a window that later
   crosses 1000px and back does not play it again. */
(function(){
  var H=document.documentElement,end=function(){H.removeAttribute('data-id-in')};
  if(!H.hasAttribute('data-id-in'))return;
  var an=[];
  [].forEach.call(document.querySelectorAll('.id,.fold--hide,.nav .on'),function(e){
    if(e.getAnimations)an=an.concat(e.getAnimations({subtree:true}))});
  if(!an.length||!window.Promise){setTimeout(end,1600);return}
  Promise.all(an.map(function(a){return a.finished})).then(end,end);
})();
/* THE HALO (the module's docstring): his portrait's orb. The dots of a
   sphere round the portrait (a Fibonacci lattice, as every orb on the site),
   turning about an axis tilted toward the reader, each lit and sized by how
   near it is. A dot over his face or behind it is never drawn, so only the
   band round the rim shows, fading in at the photo's edge. Its life is one
   number e on a critically damped spring (the site's springs, SPR): 1 is
   the turning shell, 0 every dot on the ring round the photo, the pale
   track it rests as, where the dots fade out. It is drawn on a canvas made
   for the motion and removed when it rests, with frames only while it
   moves. */
(function(){
  var H=document.documentElement;
  if(!window.requestAnimationFrame||!window.matchMedia)return;
  var calm=matchMedia('(prefers-reduced-motion: reduce)');
  if(calm.matches||matchMedia('(forced-colors: active)').matches)return;
  var fine=matchMedia('(hover: hover) and (pointer: fine)'),
      all=[],raf=0,t0=0,N=0,SX=[],SY=[],SZ=[],
      TURN=2*Math.PI/2.4;               /* the shell's turn at full life, a turn in 2.4s */
  /* one halo for each portrait: the column's, and the phone bar's, where it
     is 32px and its ring sits 2.5px out, closer, with fewer dots */
  function halo(pic,gap){
    if(!pic)return;
    var o={pic:pic,link:pic.parentNode,gap:gap,cv:null,g:null,e:0,v:0,goal:0,w:0,
           hold:0,back:0,an:0,amp:0,fade:0,last:-1e4,on:0};
    all.push(o);return o;
  }
  var col=halo(document.querySelector('.id__pic'),3.5),bar=halo(document.querySelector('.bar__pic'),2.5);
  if(!all.length)return;
  function sphere(n){               /* n dots, laid evenly on the unit sphere */
    if(N===n)return;
    N=n;SX.length=SY.length=SZ.length=0;
    for(var i=0;i<n;i++){var y=1-2*(i+.5)/n,r=Math.sqrt(1-y*y),t=i*2.399963;
      SX[i]=Math.cos(t)*r;SY[i]=y;SZ[i]=Math.sin(t)*r}
  }
  /* the canvas, over the portrait: one layout read as the motion starts */
  function lay(o){
    var p=o.pic,d=p.offsetWidth;
    if(!d)return 0;
    o.R=d/2;o.RR=o.R+o.gap;o.RS=o.RR+Math.max(3,o.R*.12);
    /* denser on a smaller sphere, so a small halo keeps its grain */
    o.n=Math.max(48,Math.round(o.RS*o.RS*(o.R>40?.1:o.R>20?.14:.24)));
    var W=Math.ceil(o.RS+4)*2,dpr=Math.min(2,window.devicePixelRatio||1);
    if(!o.cv){
      o.cv=document.createElement('canvas');o.cv.className='id__halo';
      o.cv.setAttribute('aria-hidden','true');o.g=o.cv.getContext&&o.cv.getContext('2d');
      if(!o.g){o.cv=null;return 0}
    }
    o.W=W;o.dpr=dpr;
    o.cv.width=Math.round(W*dpr);o.cv.height=Math.round(W*dpr);
    o.cv.style.width=o.cv.style.height=W+'px';
    o.cv.style.left=(p.offsetLeft+o.R-W/2)+'px';o.cv.style.top=(p.offsetTop+o.R-W/2)+'px';
    if(!o.cv.parentNode)o.link.appendChild(o.cv);
    o.col=getComputedStyle(p).getPropertyValue('--focus').trim();
    return 1;
  }
  /* The page opens: the shell stands round the portrait as the photo
     resolves, turns, and gathers into the ring. `again`: the pointer or a
     key comes to the block, and the ring breathes out a shallow shell that
     turns and settles back, fainter. */
  function play(o,again){
    var now=performance.now();
    if(!o||document.hidden||(again&&now-o.last<1600))return;
    if(!o.on&&!lay(o))return;
    o.last=now;o.on=1;sphere(o.n);
    if(again){                      /* out on the fast spring, a moment, back on the mid one */
      if(o.e<.05)o.an=now%6283/1e3;
      o.goal=.55;o.w=SPR.fast;o.hold=now+90;o.back=SPR.mid;o.amp=.62;o.fade=0;
    }else{                          /* the shell stands, turns, and gathers on the slow spring */
      o.e=1;o.v=0;o.goal=1;o.w=SPR.slow;o.hold=now+420;o.back=SPR.slow;o.amp=0;o.fade=now;o.an=.6;
    }
    soon();
  }
  function stop(o){
    o.on=0;o.e=o.v=o.goal=o.hold=0;
    if(o.cv&&o.cv.parentNode)o.cv.parentNode.removeChild(o.cv);
  }
  function soon(){if(!raf)raf=requestAnimationFrame(turn)}
  function turn(now){
    var dt=t0?Math.min(.05,(now-t0)/1e3):1/60,busy=0,i,o,d,c,x;
    raf=0;t0=now;
    for(i=0;i<all.length;i++){
      o=all[i];if(!o.on)continue;
      if(document.hidden){stop(o);continue}
      if(o.hold&&now>=o.hold){o.hold=0;o.goal=0;o.w=o.back}
      d=o.e-o.goal;c=o.v+o.w*d;x=Math.exp(-o.w*dt);
      o.e=o.goal+(d+c*dt)*x;o.v=(o.v-o.w*c*dt)*x;
      if(o.fade){o.amp=Math.min(1,(now-o.fade)/220);if(o.amp>=1)o.fade=0}
      o.an+=dt*TURN*o.e*o.e*o.e;
      if(!o.hold&&!o.goal&&o.e<.002&&Math.abs(o.v)<.02){stop(o);continue}
      draw(o);busy=1;
    }
    if(busy)raf=requestAnimationFrame(turn);else t0=0;
  }
  /* The dots: the sphere's, turned by an and tilted 22 degrees toward the
     reader, projected, and moved from the shell (e=1) onto the ring (e=0)
     along their own radius; the nearer a dot, the brighter and larger.
     None is drawn within 1px of the photo's edge, and they come in over the
     next 2.5px, so the halo never covers his face. */
  function draw(o){
    var g=o.g,C=o.W/2,e=o.e,s=e*e*(3-2*e),ca=Math.cos(o.an),sa=Math.sin(o.an),
        R=o.R,RR=o.RR,RS=o.RS,big=R>40?1:R>20?.8:.62,
        f=o.amp*Math.min(1,e/.3),     /* they fade only once nearly on the ring */
        i,px,pz,py,z,q,r,t,k,al;
    g.setTransform(1,0,0,1,0,0);g.clearRect(0,0,o.cv.width,o.cv.height);
    g.setTransform(o.dpr,0,0,o.dpr,0,0);g.fillStyle=o.col;
    for(i=0;i<N;i++){
      px=SX[i]*ca+SZ[i]*sa;pz=SZ[i]*ca-SX[i]*sa;
      py=SY[i]*.93-pz*.37;z=SY[i]*.37+pz*.93;
      q=Math.sqrt(px*px+py*py)||1e-6;
      r=RR+(RS*q-RR)*s;
      k=(r-R-1)/2.5;if(k<=0)continue;if(k>1)k=1;
      t=(z+1)/2;                    /* lit by depth on the shell, evenly on the ring */
      al=f*k*(.5+(.16+.84*t*t-.5)*s);if(al<.004)continue;
      g.globalAlpha=al;g.beginPath();
      g.arc(C+px/q*r,C+py/q*r,big*(.67+.5*(t-.5)*s),0,6.2832);g.fill();
    }
    g.globalAlpha=1;
  }
  /* page open: the column's portrait on the first page of a visit, with the
     column's arrival (data-id-in, head_js()); the phone bar's on the first
     page of a visit on a phone */
  function open(){
    if(document.hidden){document.addEventListener('visibilitychange',open);return}
    document.removeEventListener('visibilitychange',open);
    if(H.hasAttribute('data-id-in'))setTimeout(function(){play(col,0)},Math.max(0,60-performance.now()));
    else if(bar&&bar.pic.offsetWidth){
      var f=0;try{f=sessionStorage.getItem('wad:id-bar');if(!f)sessionStorage.setItem('wad:id-bar','1')}catch(e){f=1}
      if(!f)setTimeout(function(){play(bar,0)},Math.max(0,160-performance.now()));
    }
  }
  open();
  /* again, on the pointer's arrival or a key's */
  all.forEach(function(o){
    o.link.addEventListener('pointerenter',function(e){if(e.pointerType==='mouse'&&fine.matches)play(o,1)});
    o.link.addEventListener('focus',function(){if(o.link.matches(':focus-visible'))play(o,1)});
  });
  /* at rest at once where it cannot be seen: the column folded away while
     it plays, or the page put away */
  if(window.IntersectionObserver){
    var seen=new IntersectionObserver(function(es){
      for(var i=0;i<es.length;i++)if(!es[i].isIntersecting)
        for(var j=0;j<all.length;j++)if(all[j].on&&all[j].link===es[i].target)stop(all[j]);
    });
    all.forEach(function(o){seen.observe(o.link)});
  }
  addEventListener('pagehide',function(){for(var i=0;i<all.length;i++)if(all[i].on)stop(all[i])});
  if(calm.addEventListener)calm.addEventListener('change',function(){
    if(calm.matches)for(var i=0;i<all.length;i++)if(all[i].on)stop(all[i])});
})();
/* The Big Picture row (parts/bpnav.py). One spring value, p, from 0 (folded)
   to 1 (open), drives the fold; see the module's docstring. The spring is
   critically damped and integrated exactly, so a frame of any length lands
   on the curve, and a retarget keeps position and speed. The orbs (THE
   ORBS, below) share its frames. */
var H=document.documentElement,btn=document.querySelector('.nav__x');
if(!btn)return;
var fold=document.getElementById(btn.getAttribute('aria-controls')),
    list=fold&&fold.querySelector('.nav__sub');
if(!list)return;
var li=fold.parentNode,row=btn.parentNode,nav=li.parentNode,side=nav.parentNode,
    chev=btn.querySelector('.nav__chev'),tip=fold.querySelector('.nav__tip'),
    items=[].slice.call(list.querySelectorAll('a')),below=[],
    map=row.querySelector('.nav__map'),     /* the line under the row's title */
    dots=map?[].slice.call(map.querySelectorAll('.b')):[],
    segs=map?[].slice.call(map.querySelectorAll('.s')):[],
    stub=map&&map.querySelector('.v'),xs=[],len=0,S=0,
    K='wad:bp',KS='wad:bp-shown',SEEN='wad:bp-seen',
    held=li.classList.contains('nav__bp--in'),   /* a page the list holds: open with it */
    calm=matchMedia('(prefers-reduced-motion: reduce)'),
    fine=matchMedia('(hover: hover) and (pointer: fine)'),
    OUT=SPR.mid,BACK=SPR.fast,     /* the mid spring out, the fast one back */
    goal=H.getAttribute('data-bp')==='open'?1:0,p=goal,v=0,raf=0,t0=0,
    spin=0,fresh=0,                         /* the fold is moving; its first frame */
    h=0,end=0,tops=[],hts=[],pad=0,dirty=true,told=0,
    qi=[],qb=[];      /* how much of each topic, and of each bead of the line, the fold shows */
for(var n=li.nextElementSibling;n;n=n.nextElementSibling)below.push(n);

function mark(){
  btn.setAttribute('aria-expanded',goal?'true':'false');
  H.setAttribute('data-bp',goal?'open':'closed');
  fold.inert=!goal;                 /* folding away: out of the tab order at once */
}
/* the list has been seen open: the call for a look is over, on this page
   and, through wad:bp-seen, on every page after it */
function seen(){
  if(told)return;
  told=1;H.removeAttribute('data-bp-new');
  try{localStorage.setItem(SEEN,'1')}catch(e){}
}
function measure(){                 /* one layout read per toggle, none per frame */
  h=list.offsetHeight;
  end=h-(parseFloat(getComputedStyle(list,'::before').bottom)||0);
  /* a topic's place is its <li>'s, which is laid out in the list; the link
     sits at 0 inside it */
  for(var i=0;i<items.length;i++){tops[i]=items[i].parentNode.offsetTop;hts[i]=items[i].offsetHeight}
  for(i=0;i<dots.length;i++)xs[i]=dots[i].offsetLeft-dots[0].offsetLeft;
  len=xs[dots.length-1]||0;S=stub?stub.offsetHeight:0;
  dirty=false;
  if(orbs)place();
}
function paint(){
  var y=(p-1)*h,e=p*h,i,q;          /* y: what is still folded; e: the edge, in the list */
  fold.style.transform='translateY('+y+'px)';
  list.style.transform='translateY('+(-y)+'px)';
  for(i=0;i<below.length;i++)below[i].style.transform='translateY('+y+'px)';
  if(chev)chev.style.transform='rotate('+(-180*p)+'deg)';   /* down, round by the page's side, up */
  for(i=0;i<items.length;i++){      /* in once the edge has uncovered its words */
    q=(e-tops[i]-hts[i]*.55)/(Math.min(tops[i]+hts[i]+14,h)-tops[i]-hts[i]*.55);q=q<0?0:q>1?1:q;
    items[i].style.opacity=1-(1-q)*(1-q);
    items[i].style.transform='translateY('+(q-1)*6+'px)';
    qi[i]=q;
  }
  if(tip){                          /* lit by speed (full from 700px/s), held at the branch's end */
    tip.style.opacity=Math.min(1,Math.abs(v)*h/700);
    tip.style.transform='translateY('+Math.min(0,end-e)+'px)';
  }
  if(map){                          /* the line turns the corner: as far as it has run down, */
    var run=p*(h+S),hor=len-run;    /* from the first bead, it is short across the row */
    for(i=0;i<dots.length;i++){     /* a bead goes out as the line's end passes over it */
      q=(hor-xs[i]+3.5)/7;q=q<0?0:q>1?1:q;
      dots[i].style.opacity=q;dots[i].style.transform='scale('+(.5+q/2)+')';
      qb[i]=q;
    }
    for(i=0;i<segs.length;i++){
      q=(hor-xs[i]-3.5)/(xs[i+1]-xs[i]-7);q=q<0?0:q>1?1:q;
      segs[i].style.opacity=q?1:0;segs[i].style.transform='scaleX('+q+')';
    }
    if(stub){q=S?run/S:1;stub.style.transform='scaleY('+(q>1?1:q)+')'}
  }
}
function clear(){                   /* at rest nothing is left inline */
  fold.style.transform=list.style.transform=fold.style.willChange=list.style.willChange='';
  for(var i=0;i<below.length;i++)below[i].style.transform=below[i].style.willChange='';
  for(i=0;i<items.length;i++)items[i].style.opacity=items[i].style.transform='';
  for(i=0;i<dots.length;i++)dots[i].style.opacity=dots[i].style.transform='';
  for(i=0;i<segs.length;i++)segs[i].style.opacity=segs[i].style.transform='';
  if(stub)stub.style.transform='';
  if(chev)chev.style.transform='';
  if(tip)tip.style.opacity=tip.style.transform='';
}
/* the element that scrolls the column: the list on a desktop, the whole
   column in the phone drawer */
function scroller(){return getComputedStyle(nav).overflowY==='visible'?side:nav}
function cue(){
  var s=scroller();
  nav.classList.toggle('nav--more',s.scrollHeight-s.clientHeight-s.scrollTop>2);
}
/* The fold leaves the layout when it has closed. If the column is scrolled
   further than its new end, the browser would clamp it and everything would
   jump, so a spacer (the list's padding, navy on navy) takes up the
   difference; room() hands it back as the reader scrolls up. */
function keep(){
  var s=scroller(),need=Math.ceil(s.scrollTop-(s.scrollHeight-h-s.clientHeight));
  if(need>0){pad+=need;nav.style.paddingBottom=pad+'px'}
}
function room(){
  if(!pad)return;
  var s=scroller(),need=Math.max(0,Math.ceil(s.scrollTop+s.clientHeight-(s.scrollHeight-pad)));
  if(need<pad){pad=need;nav.style.paddingBottom=pad?pad+'px':''}
}
function settle(){
  if(!goal)keep();
  fold.style.display='';            /* data-bp now shows or hides it */
  clear();cue();
  if(orbs)place();
  if(goal)reveal();
  try{sessionStorage.setItem(KS,goal?'open':'closed')}catch(e){}
}
/* One frame for everything that moves: the fold's spring, then the orbs,
   which read where the fold has just put things. Frames come while the
   fold or an orb moves; at rest none are asked for. */
function frame(now){
  var dt=t0?(now-t0)/1e3:1/60,more=0;
  raf=0;t0=now;
  if(spin){
    var w=goal?OUT:BACK,f=fresh?1/60:dt,d=p-goal,c=v+w*d,x=Math.exp(-w*f);
    fresh=0;
    if(dirty)measure();
    d=p-goal;c=v+w*d;
    p=goal+(d+c*f)*x;v=(v-w*c*f)*x;
    if(Math.abs(p-goal)*h<.4&&Math.abs(v)*h<10){p=goal;v=0;spin=0;settle()}else paint();
  }
  if(orbs)more=tick(dt,now);
  if(spin||more)raf=requestAnimationFrame(frame);
  else t0=0;
}
function kick(){if(!raf)raf=requestAnimationFrame(frame)}     /* a frame soon */
function go(to,move){
  if(!to&&fold.contains(document.activeElement))btn.focus();
  goal=to?1:0;mark();
  if(goal)seen();
  fold.style.display='block';       /* laid out through the whole motion */
  measure();room();cue();           /* every read before the first write */
  if(!move||calm.matches){spin=0;p=goal;v=0;settle();if(orbs){unfold();kick()}return}
  if(!spin){
    spin=1;fresh=1;
    fold.style.willChange=list.style.willChange='transform';
    for(var i=0;i<below.length;i++)below[i].style.willChange='transform';
  }
  if(orbs)unfold();
  kick();paint();
}

/* Hover intent, where a pointer can hover and aim (a mouse, a trackpad): the
   pointer resting on the row for 350ms (moving 5px or less) opens the list
   as the chevron would, and it stays open when the pointer leaves. Closed
   with the pointer still on the row, it waits until the pointer has left
   the row and come back. A click that lands within 500ms of a hover's
   opening, the pointer still on the row, is the click the reader was
   already making, so it keeps the list open rather than folding it away
   under them; a later one closes it. A touch or a key does nothing new.
   The same rest on a row whose list is open, or will not open, plays the
   row's motion again (THE ORBS). */
var over=0,armed=1,timer=0,hx=0,hy=0,hovered=0;
/* the reader's choice holds on every page after this one (the pages the
   list holds open it all the same) */
function choose(to){
  clearTimeout(timer);timer=0;
  go(to,true);
  if(!to&&over)armed=0;
  try{localStorage.setItem(K,to?'open':'closed')}catch(e){}
}
function rest(){
  clearTimeout(timer);
  timer=setTimeout(function(){timer=0;
    if(armed&&!goal){hovered=Date.now();choose(true)}else play(0)},350);
}
row.addEventListener('pointerenter',function(e){
  if(e.pointerType!=='mouse'||!fine.matches)return;
  over=1;hx=e.clientX;hy=e.clientY;
  rest();
});
row.addEventListener('pointermove',function(e){
  if(timer&&Math.abs(e.clientX-hx)+Math.abs(e.clientY-hy)>5){hx=e.clientX;hy=e.clientY;rest()}
});
row.addEventListener('pointerleave',function(){clearTimeout(timer);timer=over=hovered=0;armed=1});
btn.addEventListener('click',function(e){
  if(goal&&e.detail&&Date.now()-hovered<500)return;
  choose(!goal);
});
li.addEventListener('keydown',function(e){
  if(e.key!=='Escape'||!goal)return;
  e.stopPropagation();              /* the drawer's Escape waits for the next press */
  choose(false);
});
/* A topic pressed by a finger or a pen lights as one under the pointer does
   (.p, the stylesheet's :active made sure, since a touch browser may paint
   :active late or not at all), from the press until the page goes; a press
   that turns into a scroll lets go, and one that led nowhere (a long press
   that opened a menu) lets go 1.5s after the finger lifts. The link is
   followed as ever: nothing here waits or stops it. */
items.forEach(function(a){
  var off=function(){a.classList.remove('p')};
  a.addEventListener('pointerdown',function(e){if(e.pointerType!=='mouse')a.classList.add('p')});
  a.addEventListener('pointercancel',off);
  a.addEventListener('pointerup',function(){setTimeout(off,1500)});
});
addEventListener('pageshow',function(){items.forEach(function(a){a.classList.remove('p')})});
/* a key that brings the reader to the row plays its motion again, once
   as focus comes in (THE ORBS) */
row.addEventListener('focusin',function(e){
  if(!row.contains(e.relatedTarget)&&e.target.matches&&e.target.matches(':focus-visible'))play(0);
});

/* The call for a look (the module's docstring): it starts once the row is
   on screen (the desktop's column shown, the phone's drawer open), with the
   thought's arrival at the chevron (THE ORBS), every 6s from then, and rests
   while the row is off screen or the tab is hidden. Where no orb can be
   drawn it starts once the page has been up 1.2s. The list seen open ends
   it (data-bp-new goes, which the stylesheet asks for). */
var called=0,shown=1,asks=H.hasAttribute('data-bp-new')&&!goal&&!calm.matches;
function call(){
  if(called||goal||!H.hasAttribute('data-bp-new'))return;
  called=1;li.classList.add('nav__bp--call');
}
function still(){li.classList.toggle('nav__bp--still',!shown||document.hidden)}
var waiting=0,when=function(){
  if(!waiting){waiting=1;setTimeout(call,Math.max(300,1200-performance.now()))}};
if(asks)document.addEventListener('visibilitychange',still);
function scrolled(){room();cue()}
nav.addEventListener('scroll',scrolled,{passive:true});
side.addEventListener('scroll',scrolled,{passive:true});
addEventListener('resize',function(){dirty=true;moved=1;cue()});
/* back from the back-forward cache: the reader may have chosen, or seen the
   list, on another page; a page the list holds keeps it as it was */
addEventListener('pageshow',function(e){
  if(!e.persisted)return;
  var s=null,m=null;try{s=localStorage.getItem(K);m=localStorage.getItem(SEEN)}catch(x){}
  if(m)seen();
  if(!held&&(s==='open'||s==='closed')&&(s==='open')!==!!goal)go(s==='open',false);
});
/* the topic the page is filed under: when it lies below the column's fold
   (a short window), the column scrolls to it, at once, clear of the fade at
   its foot */
function reveal(){
  var a=goal&&list.querySelector('a[aria-current]');
  if(!a)return;
  var s=scroller(),r=a.getBoundingClientRect(),box=s.getBoundingClientRect(),
      past=r.bottom-Math.min(box.bottom,innerHeight)+32;
  if(past>0)s.scrollTop+=past;
}

/* ------------------------------------------------------------------------
   THE ORBS (the module's docstring). One canvas over the row and its list,
   drawn only while something moves and cleared at rest. Each bead of the
   line and each topic's bead has an orb: a sphere of 48 dots (a Fibonacci
   lattice, so they lie evenly), turning about an axis tilted toward the
   reader, each dot lit and sized by how near it is. An orb's life is one
   number, its excitation e, on a critically damped spring (the site's
   springs, SPR): 0 is the still bead, 1 the thinking orb. It turns at a
   speed that goes as e cubed, so it spins up as it wakes and down to a stop
   as it settles. The thought is one white point in a soft light of the
   column's own (--nav-ink, --nav-mute; warm stays with "you are here" and
   the chevron), with a short tail: it runs the line, rides the tip of the
   branch as the list opens, and runs down the branch to a topic under the
   pointer or a finger. Nothing here runs under prefers-reduced-motion or
   forced colours, or without a canvas: the row is then as the stylesheet
   draws it.
   ------------------------------------------------------------------------ */
var orbs=0,cv,g,dpr=1,LY=0,BY=0,CX=0,CY=0,moved=1,
    BX=[],IY=[],nb=dots.length,ni=items.length,no=dots.length+items.length,
    N=48,SX=[],SY=[],SZ=[],
    E=[],EV=[],ET=[],EW=[],EH=[],AN=[],PIN=[],HERE=[],OC=[],WOKE=[],
    INK='',MUTE='',WARM='',O2=[0,0],
    QX=[],QY=[],QD=[],QA=0,QB=0,    /* the thought's way along the line and on to the chevron */
    P=0,PT=0,PX=0,PY=0,PA=0,PG=0,PS=0,TV=0,     /* the thought: its errand, when it set out, where, how bright */
    HK=-1,LT=0,LV=0,LG=0,LA=0,LF=0,HA=0,HT=0,LW=0,  /* a topic aimed at: the lit path's tip, speed, goal, light, spring */
    introd=0,lastPlay=-1e4,ovis=1,
    TA=560,TB=270,RAMP=.25,         /* the line, and on to the chevron (ms); easing in over a quarter */
    WAKE=SPR.fast,REST=SPR.draw,HOLD=120,SPIN=2*Math.PI/1.1,
    AIM=SPR.fast,PRESS=SPR.quick;   /* the lit path: under the pointer, under a finger */

function orbsOn(){
  if(calm.matches||!nb||matchMedia('(forced-colors: active)').matches)return;
  cv=document.createElement('canvas');
  g=cv.getContext&&cv.getContext('2d');
  if(!g)return;
  cv.className='nav__orbs';cv.setAttribute('aria-hidden','true');
  li.appendChild(cv);li.classList.add('nav__bp--orbs');
  for(var i=0;i<N;i++){
    var y=1-2*(i+.5)/N,r=Math.sqrt(1-y*y),t=i*2.399963;
    SX[i]=Math.cos(t)*r;SY[i]=y;SZ[i]=Math.sin(t)*r;
  }
  var on=row.firstElementChild.classList.contains('on');
  for(i=0;i<no;i++){
    E[i]=EV[i]=ET[i]=EH[i]=PIN[i]=OC[i]=WOKE[i]=0;EW[i]=WAKE;AN[i]=i*1.9;
    HERE[i]=i<nb?on&&dots[i].classList.contains('h'):items[i-nb].hasAttribute('aria-current');
  }
  orbs=1;tokens();
  if(goal)measure();else place();
  items.forEach(function(a,k){
    a.addEventListener('pointerenter',function(e){if(e.pointerType==='mouse'&&fine.matches)aim(k,0)});
    a.addEventListener('pointerleave',function(e){if(e.pointerType==='mouse')loose(k,0)});
    /* a finger or a pen: the press is the hover it cannot have */
    a.addEventListener('pointerdown',function(e){if(e.pointerType!=='mouse')aim(k,2)});
    a.addEventListener('pointercancel',function(){loose(k,0)});
    a.addEventListener('pointerup',function(e){
      if(e.pointerType!=='mouse')setTimeout(function(){loose(k,0)},1500)});
    a.addEventListener('focus',function(){if(a.matches(':focus-visible'))aim(k,1)});
    a.addEventListener('blur',function(){loose(k,1)});
  });
  list.addEventListener('pointerleave',function(){LF=0;HT=0;kick()});
  addEventListener('pagehide',hush);
  /* asked for less motion while the page is open: the orbs go, and stay gone */
  if(calm.addEventListener)calm.addEventListener('change',function(){
    if(!calm.matches||!orbs)return;
    hush();orbs=0;li.removeChild(cv);li.classList.remove('nav__bp--orbs');
  });
}
function tokens(){
  var s=getComputedStyle(H);
  INK=s.getPropertyValue('--nav-ink').trim();MUTE=s.getPropertyValue('--nav-mute').trim();
  WARM=s.getPropertyValue('--accent-on-nav').trim();
}
/* where the beads are, in the <li>'s frame: one layout read, at a toggle,
   a resize or the fonts' arrival. The canvas is the <li>'s own box (the
   stylesheet sizes it), so it never reaches past the column's last row;
   only its pixels are set here, at the device's ratio (2 at most). */
function place(){
  var a=row.firstElementChild,i,w=li.offsetWidth,hh=li.offsetHeight,mx,my;
  LY=fold.offsetTop;
  if(map){
    mx=a.offsetLeft+map.offsetLeft;my=a.offsetTop+map.offsetTop;
    for(i=0;i<nb;i++)BX[i]=mx+dots[i].offsetLeft+dots[i].offsetWidth/2;
    BY=my+map.offsetHeight/2;
  }
  CX=btn.offsetLeft+btn.offsetWidth/2;CY=btn.offsetTop+btn.offsetHeight/2;
  /* a topic's bead is on its words' line, which is the link's middle
     unless a note under the words makes the link taller */
  if(list.offsetHeight)for(i=0;i<ni;i++)IY[i]=items[i].parentNode.offsetTop+
    items[i].firstElementChild.offsetTop+items[i].firstElementChild.offsetHeight/2;
  dpr=Math.min(2,window.devicePixelRatio||1);
  w=Math.round(w*dpr);hh=Math.round(hh*dpr);
  if(cv.width!==w||cv.height!==hh){cv.width=w;cv.height=hh}
  way();moved=0;
}
/* the thought's way: along the line from the first bead to the last, then
   on at the line's level and up into the chevron's middle */
function way(){
  var x0=BX[0],x1=BX[nb-1],i,t,u,x,y,c1=x1+(CX-x1)*.5,c2=CX-(CX-x1)*.1,cy=CY+(BY-CY)*.6;
  QX.length=QY.length=QD.length=0;
  QX.push(x0,x1);QY.push(BY,BY);QD.push(0,x1-x0);QA=x1-x0;
  for(i=1;i<=16;i++){
    t=i/16;u=1-t;
    x=u*u*u*x1+3*u*u*t*c1+3*u*t*t*c2+t*t*t*CX;
    y=u*u*u*BY+3*u*u*t*BY+3*u*t*t*cy+t*t*t*CY;
    QD.push(QD[QD.length-1]+Math.sqrt((x-QX[QX.length-1])*(x-QX[QX.length-1])+(y-QY[QY.length-1])*(y-QY[QY.length-1])));
    QX.push(x);QY.push(y);
  }
  QB=QD[QD.length-1]-QA;
}
function at(s){                     /* the point s along the way, into O2 */
  for(var i=1;i<QD.length-1&&QD[i]<s;i++);
  var f=(s-QD[i-1])/((QD[i]-QD[i-1])||1);f=f<0?0:f>1?1:f;
  O2[0]=QX[i-1]+(QX[i]-QX[i-1])*f;O2[1]=QY[i-1]+(QY[i]-QY[i-1])*f;
}
/* easing in over the first a of the way, then even */
function ramp(u,a){return (u<a?u*u/(2*a):u-a/2)/(1-a/2)}
/* easing in and out over a at each end, even between */
function glide(u,a){var k=1/(1-a);return u<a?k*u*u/(2*a):u>1-a?1-k*(1-u)*(1-u)/(2*a):k*(u-a/2)}

/* The row comes alive (the module's docstring): the thought runs the line,
   waking each bead as it reaches it, and on into the chevron; or, the list
   open, down the branch through each topic. Once a page view by itself,
   when the row is first on screen; again when the reader rests the pointer
   on the row or a key brings focus to it, not within 1.6s of the last. */
function play(first){
  if(!orbs||spin||P===1||P===2||document.hidden)return 0;
  var now=performance.now(),k;
  if(!first&&now-lastPlay<1600)return 0;
  lastPlay=now;tokens();
  if(moved)place();
  if(goal){
    if(!list.offsetHeight||!ni)return 0;
    for(k=0;k<ni;k++)WOKE[nb+k]=0;
    P=2;TV=Math.max(360,(LY+IY[ni-1]-BY)/.42);   /* 420px a second */
  }else{
    for(k=0;k<nb;k++)WOKE[k]=0;
    P=1;PG=0;
  }
  PT=-1;kick();return 1;
}
function intro(){
  if(introd||!orbs)return;
  if(document.hidden){document.addEventListener('visibilitychange',intro);return}
  document.removeEventListener('visibilitychange',intro);
  introd=1;
  /* 0.22s into the page, or 0.56s on the first page of a visit, where it
     follows the column's arrival down from the portrait */
  var go1=function(){setTimeout(function(){
    tokens();if(moved)place();play(1);
  },Math.max(120,(H.hasAttribute('data-id-in')?560:220)-performance.now()))};
  if(document.fonts&&document.fonts.ready)document.fonts.ready.then(go1,go1);else go1();
}
/* the thought reaches the chevron: the first call for a look begins, or,
   the question answered long ago, the chevron gives once, as under the
   pointer */
function arrive(){
  if(goal)return;
  if(H.hasAttribute('data-bp-new')){call();return}
  var cv0=chev&&chev.parentNode;
  if(cv0&&cv0.animate)cv0.animate([{translate:'0 0',easing:'cubic-bezier(.3,0,.2,1)'},
    {translate:'0 2.4px',offset:.33,easing:'cubic-bezier(.2,.8,.2,1)'},{translate:'0 0'}],{duration:380});
}
/* a fold begins: the thought rides the tip of the branch, and the topics
   wake as the edge uncovers them */
function unfold(){
  var k,now=performance.now();
  if(goal)for(k=0;k<ni;k++)WOKE[nb+k]=0;
  else{for(k=0;k<ni;k++)if(PIN[nb+k]){PIN[nb+k]=0;EH[nb+k]=now}HK=-1;LF=HT=0}
  if(P===1||P===2)P=0;
}
/* an orb wakes, and holds a moment before it settles */
function wake(j,now){
  if(ET[j]!==1){ET[j]=1;EW[j]=WAKE}
  EH[j]=now+HOLD;
  if(!HERE[j])bead(j,1);
}
/* the stylesheet's bead gives way to its orb (.o), and comes back */
function bead(j,on){
  if(OC[j]===on)return;
  OC[j]=on;(j<nb?dots[j]:items[j-nb]).classList.toggle('o',!!on);
}
/* how much of orb j's bead shows, as the fold stands */
function shows(j){return j<nb?(spin?qb[j]:goal?0:1):(spin?qi[j-nb]:goal?1:0)}
/* A topic under the pointer, a finger or a key: the path lights from the
   row's line down the branch, the thought riding its tip, and the topic's
   orb wakes as it arrives and stays alive while the topic is pointed at.
   A key (mode 1) takes the path and the orb at once. A finger (mode 2)
   wakes the orb at once and sends the thought down on the quick spring, so
   both show before the page it opens has come. The topic the page is filed
   under takes none of it, as it takes none of the stylesheet's. */
function aim(k,mode){
  if(!orbs||HERE[nb+k]||!IY.length)return;
  var j=nb+k;
  if(moved)place();
  tokens();
  if(P===2)P=0;
  PIN[j]=1;LG=LY+IY[k];LF=1;
  if(mode===1){LT=LG;LV=0;LA=1;E[j]=ET[j]=1;EV[j]=0;EH[j]=0;bead(j,1)}
  else{
    if(LA<=0){LT=BY;LV=0}HK=k;HT=1;LW=mode?PRESS:AIM;
    if(mode)wake(j,performance.now());
  }
  kick();
}
function loose(k,key){
  var j=nb+k;
  if(!orbs||!PIN[j])return;
  PIN[j]=0;EH[j]=performance.now();
  if(k===HK)HK=-1;
  if(key){E[j]=ET[j]=0;EV[j]=0;EH[j]=0;bead(j,0);if(HK<0){LA=LF=0}}
  kick();
}
/* everything to rest at once: a hidden column, a page put away */
function hush(){
  if(!orbs)return;
  if(P===1&&!PG)arrive();
  P=0;PA=HA=HT=LA=LF=0;HK=-1;
  for(var j=0;j<no;j++){E[j]=ET[j]=EV[j]=EH[j]=PIN[j]=0;bead(j,0)}
  if(g)g.clearRect(0,0,cv.width,cv.height);
}
/* one step of every orb and of the thought; says whether a frame is
   needed: 1 while anything moves, 0 at rest */
function tick(dt,now){
  var busy=0,j,k,d,c,x,w,t,s,y,u;
  if(moved)place();
  if(PT<0)PT=now;                   /* timed from its first frame, on the frames' clock */
  /* the thought along the line, and on into the chevron: in 90ms, along
     in TA, round in TB, and out in 140ms */
  if(P===1){
    t=now-PT;
    if(t<TA)s=QA*ramp(t/TA,RAMP);
    else if(t<TA+TB){u=(t-TA)/TB;s=QA+QB*((QA/(TA*(1-RAMP/2)))*TB/QB*(u*u*u-2*u*u+u)+3*u*u-2*u*u*u)}
    else{s=QA+QB;if(!PG){PG=1;arrive()}}
    at(s);PX=O2[0];PY=O2[1];PS=s;
    PA=t<90?t/90:t>TA+TB?Math.max(0,1-(t-TA-TB)/140):1;
    for(k=0;k<nb;k++)if(!WOKE[k]&&s>=BX[k]-BX[0]-3){WOKE[k]=1;wake(k,now)}
    if(t>TA+TB+140)P=0;
    busy=1;
  }
  /* down the branch, through each topic */
  else if(P===2){
    t=now-PT;u=t/TV;u=u>1?1:u;
    PX=BX[0];PY=BY+(LY+IY[ni-1]-BY)*glide(u,.22);
    PA=t<90?t/90:t>TV?Math.max(0,1-(t-TV)/140):1;
    for(k=0;k<ni;k++)if(!WOKE[nb+k]&&PY>=LY+IY[k]-3){WOKE[nb+k]=1;wake(nb+k,now)}
    if(t>TV+140)P=0;
    busy=1;
  }
  /* the fold carries it at the tip of the branch */
  if(spin&&P!==1&&P!==2){
    y=p*h;P=3;PX=BX[0];PY=LY+Math.min(end,y)-2.5;
    PA=Math.min(1,Math.abs(v)*h/700);
    if(goal)for(k=0;k<ni;k++)if(!WOKE[nb+k]&&y>=IY[k]){WOKE[nb+k]=1;wake(nb+k,now)}
  }else if(P===3){P=0;PA=0}
  /* the lit path to a topic under the pointer or a finger, on its spring;
     the orb wakes as the thought is nearly there (the last 12%, or 6px) */
  if(LF||LA>0){
    if(HK>=0||LT!==LG){
      w=LW||AIM;d=LT-LG;c=LV+w*d;x=Math.exp(-w*dt);LT=LG+(d+c*dt)*x;LV=(LV-w*c*dt)*x;
      if(Math.abs(LT-LG)<.3&&Math.abs(LV)<8){LT=LG;LV=0}
    }
    LA=LF?1:Math.max(0,LA-dt/.12);
    if(HK>=0&&Math.abs(LT-LG)<Math.max(6,.12*Math.abs(LG-BY))){
      j=nb+HK;if(ET[j]!==1||!OC[j])wake(j,now);HT=0}
    HA=HT?Math.min(1,HA+dt/.06):Math.max(0,HA-dt/.12);
    if(!LA){LT=BY;LV=0}
    busy=1;
  }
  /* the orbs' springs: awake, a moment, then back to the still bead */
  for(j=0;j<no;j++){
    if(ET[j]===1&&EH[j]&&now>=EH[j]&&!PIN[j]){ET[j]=0;EW[j]=REST;EH[j]=0}
    d=E[j]-ET[j];
    if(d||EV[j]){
      w=EW[j];c=EV[j]+w*d;x=Math.exp(-w*dt);E[j]=ET[j]+(d+c*dt)*x;EV[j]=(EV[j]-w*c*dt)*x;
      if(Math.abs(E[j]-ET[j])<.002&&Math.abs(EV[j])<.02){E[j]=ET[j];EV[j]=0}
      busy=1;
    }
    if(ET[j]===1)busy=1;
    if(OC[j]&&ET[j]!==1&&E[j]<.35)bead(j,0);
    AN[j]+=dt*SPIN*E[j]*E[j]*E[j];
  }
  if(PA>0||HA>0)busy=1;
  draw();
  return busy;
}
function draw(){
  var j,al,y,k;
  g.setTransform(1,0,0,1,0,0);g.clearRect(0,0,cv.width,cv.height);
  g.setTransform(dpr,0,0,dpr,0,0);
  if(LA>0){                         /* the lit path: the column's light, from the row's line down */
    g.globalAlpha=LA;g.fillStyle=MUTE;g.fillRect(BX[0]-.5,BY,1,LT-BY);
  }
  for(j=0;j<no;j++){
    if(E[j]<=0)continue;
    al=shows(j);if(al<=0)continue;
    if(j<nb)orb(BX[j],BY,E[j],AN[j],HERE[j],al);
    else{k=j-nb;y=LY+IY[k]+(spin?(qi[k]-1)*6:0);orb(BX[0],y,E[j],AN[j],HERE[j],al)}
  }
  if(PA>0){
    if(P===1)tail1();else tail(PX,PY,PA);
    spark(PX,PY,PA);
  }
  if(HA>0&&LA>0){tail(BX[0],LT,HA);spark(BX[0],LT,HA)}
  g.globalAlpha=1;
}
/* an orb: its dots on a sphere of radius r, turned by a and tilted 22
   degrees toward the reader; the nearer a dot, the brighter and larger.
   From a still bead (e=0) it grows out of the bead's ring and settles back
   into it; "you are here" is warm, keeps its bead as a core, and hides the
   dots behind it. */
function orb(x,y,e,a,warm,al){
  var s=e*e*(3-2*e),r=warm?3.5+3*s:3+3.5*s,ca=Math.cos(a),sa=Math.sin(a),i,px,pz,py,z,t;
  g.fillStyle=warm?WARM:INK;
  for(i=0;i<N;i++){
    px=SX[i]*ca+SZ[i]*sa;pz=SZ[i]*ca-SX[i]*sa;
    py=SY[i]*.93-pz*.37;z=SY[i]*.37+pz*.93;
    if(warm&&z<0&&(px*px+py*py)*r*r<13)continue;
    t=(z+1)/2;
    g.globalAlpha=al*s*(warm?.45+.55*t:.14+.86*t*t);
    g.beginPath();g.arc(x+px*r,y+py*r,warm?.3+.32*t:.24+.36*t,0,6.2832);g.fill();
  }
}
/* the thought: a white point in a soft light of the column's own */
function spark(x,y,a){
  g.fillStyle=MUTE;
  g.globalAlpha=a*.14;g.beginPath();g.arc(x,y,4,0,6.2832);g.fill();
  g.globalAlpha=a*.32;g.beginPath();g.arc(x,y,2.4,0,6.2832);g.fill();
  g.fillStyle=INK;
  g.globalAlpha=a;g.beginPath();g.arc(x,y,1.5,0,6.2832);g.fill();
}
/* its tail, 28px of the line behind it, fading */
function tail(x,y,a){             /* up the branch */
  g.fillStyle=MUTE;
  for(var k=0;k<7;k++){g.globalAlpha=a*(1-k/7)*.8;g.fillRect(x-.5,y-4*(k+1),1,4)}
}
function tail1(){                   /* back along the way it came */
  var k,x,y;
  g.strokeStyle=MUTE;g.lineWidth=1;
  for(k=0;k<7;k++){
    at(Math.max(0,PS-4*k));x=O2[0];y=O2[1];
    at(Math.max(0,PS-4*(k+1)));
    g.globalAlpha=PA*(1-k/7)*.8;g.beginPath();g.moveTo(x,y);g.lineTo(O2[0],O2[1]);g.stroke();
  }
}

/* start: the orbs, then the row coming alive when it is first on screen;
   the call for a look rests while it is not */
orbsOn();
if(window.IntersectionObserver){
  var io=new IntersectionObserver(function(es){
    for(var i=0;i<es.length;i++){
      var r=es[i];
      if(r.target===row){
        shown=r.intersectionRatio>=.01;if(asks)still();
        if(r.intersectionRatio>=.9){if(orbs)intro();else if(asks)when()}
      }else{ovis=r.isIntersecting;if(!ovis)hush();else if(orbs)kick()}
    }},{threshold:[0,.01,.9]});
  io.observe(row);if(orbs)io.observe(li);
}else if(orbs)intro();else if(asks)when();
document.addEventListener('visibilitychange',function(){if(!document.hidden&&orbs)kick()});
addEventListener('pageshow',function(e){if(e.persisted&&orbs)kick()});

mark();
/* shown open, or on the Big Picture page, the list has been seen */
if(goal||li.classList.contains('nav__bp--here'))seen();
reveal();
var arrive0=H.getAttribute('data-bp-go');
if(arrive0){                        /* after the first paint, which shows the list as the reader left it */
  H.removeAttribute('data-bp-go');introd=1;
  try{sessionStorage.setItem('wad:bp-arrived','1')}catch(e){}
  requestAnimationFrame(function(){requestAnimationFrame(function(){go(arrive0==='open',true)})});
}else{try{sessionStorage.setItem(KS,goal?'open':'closed')}catch(e){}}
cue();
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(function(){dirty=true;moved=1;cue();reveal()});
"""

# The springs' rates, from the tokens (parts/springs.py): Motion's spring()
# of visual duration v, bounce 0, is critically damped at w = 2 pi / 1.2v.
SPRING_RATES = {name: round(2 * math.pi / (1.2 * visual / 1000), 2)
                for name, (visual, _, _) in SPRINGS.items()}
JS = JS.replace("/*SPR*/", "{" + ",".join(f"{k}:{v}" for k, v in SPRING_RATES.items()) + "}")


def render(**_kw):
    """The column is written by build.py's shell(); this part adds no page markup."""
    return ""
