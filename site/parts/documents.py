"""Documents: the Big Picture of Waves and Data Analytics (big-picture.html).

The page the column's Big Picture row opens: every document and slide deck on
the site, under the topic it belongs to, and how his topics hang together.

Round 11 (27 Sep 2026). The professor kept round 10's line ("daha guzel
olmus, daha az yer kaplamis") and asked for three things, which make the
page:

  - Five topics, in his order, the foundation first and the code last:
    Probability & Statistics (the foundation), Signal Processing & System ID,
    Machine Learning (really a continuation of system identification, he
    says), Waves and Dynamics (which all of the above serve), and Python /
    Programming ("in the end we code everything"). They stand side by side
    as the columns of one table. Over their heads a line runs through a node
    for each, numbered 1 to 5 as he numbered them, and each concept two
    topics share is an arc from node to node carrying its word (_BRIDGES).
  - His research is no longer a column. Under the five, a brace spans all of
    them and carries his sentence, "My research involves all of these.", and
    his research documents stand under it, with the way to My Research Areas.
  - The shelf is gone ("karmasik olmus"): each document and deck is a card
    (its picture, its title, its length) directly under its topic, so a
    reader knows what to open in which section. Nothing is listed twice.

Under 920px of its width the table stands upright: the topics one under
another on a spine, each followed by its cards, the arcs at their side.

Motion (round 15, 29 Sep 2026: the site's thinking orbs, tools/ROUND15.md).
The page speaks the column's language (parts/bpnav.py, its Big Picture row):
a point, the thought, travels a line, and a topic it reaches thinks, its
node a small sphere of dots that turns and settles back into its numbered
ring. Each motion says something, once, and then the page is still:

  - the arrival, with the line on screen: the thought runs the line from 1
    to 5, drawing it, and each node is born as it arrives, thinks and rests
    as its ring, its topic settling in under it. Near the fifth a point sets
    out along each bridge from its first topic to its second, drawing it,
    and writes the bridge's word as it passes under it (a thin band of blue
    runs through the word with the point). About 1.5s;
  - his research: the brace, once in view, opens from its point, and a
    point runs out along it and up into each of the five, "involves all of
    these"; pointing at one of his research documents runs them again;
  - a topic in hand (pointed at, tabbed into, tapped, or arrived at from a
    link): its column fills and its rule draws, its node thinks and settles
    into the lit node, and a point runs along each bridge it shares,
    lighting the bridge and its word behind it, so each topic at a far end
    thinks a moment and lights as its point arrives. The rest dims;
  - a card under the pointer or a key: its title's underline draws through
    its lines, a hairline of blue opens under its picture, and its arrow
    springs. It never lifts or casts a shadow (DESIGN_BRIEF 4).

The animations keep to the page's inks and link blue: the client disliked
orange in them. Travel is on Motion's springs (parts/springs.py) or on the
script's critically damped ones; frames are asked for only while something
moves, none off screen or in a hidden tab, and the orbs' canvases are at the
device's ratio, 2 at most. Upright (a phone), the topics settle in and each
node thinks, and each word shimmers, once as it comes into view. Asked for
less motion, the page shows the end states at once; with colours forced,
the plain drawing.

His words: the topics' lines are his, as slide 1's column sets them (build.NAV
carries the same words, and nav_report() holds those to the slide); the
documents' titles are their pages' <h1>s, the decks' titles his slide 1 and
his research text; the sentence under the brace is his (27 Sep 2026). The
caption and the line under the page's title are ours.

The pictures are content/bigpicture/, which tools/bp_art.py cuts from his
documents and decks for the card's 16:9 box; build.py copies them to art/ and
passes their sizes (`art`), so each has its width and height and nothing
moves as they load. A card without a picture shows its words alone.
"""

import html
import json
import os
import re

__all__ = ["CSS", "JS", "CATEGORIES", "RESEARCH", "DECKS", "RESEARCH_DECKS", "families",
           "render_big_picture"]

# his three guides and the short piece
_VW = "dynamical-behavior-of-engineering-structures-and-acoustic-wave-propagation"
_SP = "signal-processing-system-identification-and-optimization"
_ML = "machine-learning-the-complete-picture-and-guide-5"
_FB = "from-bridges-to-photons"

# The Big Picture's topics, in the professor's order (27 Sep 2026: "prob stat
# estimation temel, sonra signal proce system id, sonra machine learning ...,
# sonra waves and dynamics ..., sonda da python/programming"): each with the
# whole documents that cover it, the decks (`decks`, the deck pages that cover
# it), or the page in preparation that stands for it, and `line`, his own line
# for the topic from the column of his slide 1. The column's Big Picture list
# is built from this too (parts/bpnav.py): it names each by `short` where
# there is one. The ids are the places the home page's list links to.
CATEGORIES = [
    dict(id="probability-statistics", label="Probability & Statistics", docs=[], soon=None,
         decks=["probability-statistics.html"], line="Stochastic Process, Estimation"),
    dict(id="signal-processing", label="Signal Processing, System Identification, Estimation Theory, Optimization",
         short="Signal Processing & System ID",
         docs=[_SP], soon=None,
         line="Estimation, Inverse Problems, Optimization, Machine Learning"),
    dict(id="machine-learning", label="Machine Learning", docs=[_ML], soon=None,
         line="Neural and non-neural methods, Data Science vs ML Engineer"),
    dict(id="waves-dynamics", label="Waves and Dynamics", docs=[_VW, _FB], soon=None,
         line="All vibrations are waves"),
    dict(id="python-programming", label="Python / Programming", docs=[],
         soon="python-programming.html", line=""),
]

# the three documents of his research, under the brace
RESEARCH = ("brochure-shm-and-ndt-2-pages", "understanding-shm-and-ndt",
            "sound-detection-and-tracking")

def _slides(folder, fallback):
    """How many slides a deck has, counted as build.py counts the ones it
    writes: one <stem>-1600.webp each in content/<folder>/web (s004, and
    s065a for a slide of ours lettered after his 65). The number given stands
    in where that folder is missing."""
    web = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                       "content", folder, "web")
    try:
        count = sum(1 for f in os.listdir(web) if re.fullmatch(r"s\d{3}[a-z]*-1600\.webp", f))
    except OSError:
        return fallback
    return count or fallback


# His decks, a presenter each (parts/deck.py): href -> (title, note, slide
# count). The titles are his: slide 1 of the probability deck, and his name
# for the research one. The notes are ours. build.py passes the counts it
# finds; these stand in for a render outside the build, read from the same
# slides (the probability deck has 74: his 73 and our Kalman loop, 65a,
# 29 Sep 2026).
DECKS = {
    "probability-statistics.html": ("Probability, statistics and estimation",
                                    "Opens with a big-picture map of the subject.",
                                    _slides("deck-probstat", 74)),
    "presentation.html": ("Extensive ppt regarding my MSc and PhD Research",
                          "The master's and PhD work, in more depth.", _slides("deck-phd", 177)),
}
RESEARCH_DECKS = ("presentation.html",)   # after RESEARCH's three documents

# Titles and notes for a render outside the build; build.py passes its DOCS,
# where each document is named by the <h1> of its page. The notes are ours
# (the page no longer shows them; parts/soon.py does).
_DOCS = {
    RESEARCH[0]: ("Structural Health Monitoring (SHM) and Non-destructive Testing (NDT)",
                  "A two-page introduction to both fields."),
    RESEARCH[1]: ("Understanding Structural Health Monitoring and Nondestructive Testing: "
                  "A Casual Introduction", "The same ground, at length."),
    RESEARCH[2]: ("Understanding Sound Classification, Localization and Tracking and "
                  "Similarity to NDT", "Acoustic wave-based monitoring."),
    _VW: ("Dynamical Behavior of Engineering Structures and Acoustic Wave Propagation",
          "The vibrations and waves guide."),
    _SP: ("Signal Processing, System Identification, Estimation Theory and Optimization "
          "with the underlying logic of machine learning", "The data side of the work."),
    _ML: ("Machine Learning",
          "Twelve sections, from what machine learning is to how to learn it."),
    _FB: ("From Bridges to Photons: Mode Shapes and Wave Propagation in Quantum Mechanics",
          "A short piece."),
}

# pages in his Word file (Word's own count), shown so a reader knows the length
_PAGES = {"brochure-shm-and-ndt-2-pages": 1, "understanding-shm-and-ndt": 11,
          "sound-detection-and-tracking": 5, _VW: 20, _SP: 18, _ML: 44, _FB: 3}

# the home page's icon for each topic (parts/topics.py)
_ICON_OF = {"waves-dynamics": "vibrations-waves", "signal-processing": "signal-processing",
            "machine-learning": "machine-learning", "probability-statistics": "probability-statistics",
            "python-programming": "python-programming"}

# each topic's short mark, for the stylesheet
_AREA = {"probability-statistics": "pr", "signal-processing": "sp", "machine-learning": "ml",
         "waves-dynamics": "wd", "python-programming": "py"}

# His sentence under the five (27 Sep 2026: "my research involves all of these
# diyelim"), and our name for the way on, the column's own row.
RESEARCH_LINE = "My research involves all of these."
_MORE = ("research.html", "My Research Areas")

# The bridges: a concept two topics share, named by a word both topics' own
# texts use, so the line shows his "Aha!" instead of asserting a link. In his
# order the first two join neighbours; the third reaches over Machine
# Learning. Where his words are:
#   Estimation: his column's sub-lines, "Stochastic Process, Estimation" and
#     "Estimation, Inverse Problems, Optimization, Machine Learning"; his deck's
#     title, and slide 61, "Estimation theory: designing rules for unknown
#     quantities".
#   Optimization: the signal processing guide's title, "...Estimation Theory
#     and Optimization with the underlying logic of machine learning"; the
#     machine learning guide, "Gradient Descent: The optimization algorithm."
#   Mode Shapes: the signal processing guide, "most of my own work has
#     involved identifying structural systems, meaning their resonance
#     frequencies, mode shapes, and damping ratios"; the vibrations guide on
#     mode shapes throughout, and the title of From Bridges to Photons.
# Round 10's Wave Propagation and System Identification joined his research,
# which is no longer a topic; Regression (Machine Learning and Probability &
# Statistics) would cross Mode Shapes, and fewer, clearer arcs read faster.
# None touches Python / Programming: the line itself ends there.
_BRIDGES = (
    ("Estimation", "probability-statistics", "signal-processing"),
    ("Optimization", "signal-processing", "machine-learning"),
    ("Mode Shapes", "signal-processing", "waves-dynamics"),
)

CSS = """
/* ---------- the Big Picture ---------- */
.bp{padding-bottom:24px}
/* the page runs wider than prose, for its table of five topics */
.wrap.bp{max-width:1240px}
.bp__lede{max-width:var(--measure)}
/* a line for a screen reader only */
.bp__vh{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%%);white-space:nowrap}

/* THE TABLE OF TOPICS (round 11). The figure is its own container. From
   920px of its width his five topics stand side by side in his order, the
   columns of one table; over their heads a line runs through a numbered
   node for each, and every concept two topics share is an arc from node to
   node carrying its word (the line, ticks and arcs are drawn by the script
   from where the type put the nodes). A column's rows (its name, his line,
   its cards) are the table's rows, so the cards start level. Narrower, the
   topics stand one under another on a spine, each followed by its cards. */
.bpm{container:bpm/inline-size;position:relative;max-width:none;margin:clamp(16px,2.4vw,28px) 0 0}
.bpm__stage{--bpm-mode:wide;--band:106px;position:relative;display:grid;
  grid-template-columns:repeat(5,minmax(0,1fr));grid-template-rows:auto auto 1fr;
  padding-top:var(--band)}
.bpm__stage::before{content:"";position:absolute;left:0;right:0;top:var(--band);height:1px;
  background:color-mix(in oklab,var(--ink) 70%%,var(--page))}
.bpm__edges{position:absolute;inset:0;z-index:1;width:100%%;height:100%%;overflow:visible;
  pointer-events:none}
.bpm__words{position:absolute;inset:0;z-index:3;pointer-events:none}

/* a topic, a column of the table: pointed at or tabbed into, it fills from
   the top on Motion's spring and the rule over it draws in the page's lit
   blue (round 15: the animations keep to the blues and inks) */
.bpm__n{position:relative;z-index:2;min-width:0;grid-row:span 3;display:grid;
  grid-template-rows:subgrid;padding:18px 14px 24px;isolation:isolate;
  border-left:1px solid var(--rule);scroll-margin-top:calc(var(--band) + 24px);
  -webkit-tap-highlight-color:transparent;transition:opacity var(--t-fast) var(--ease-state)}
.bpm__stage>.bpm__n:first-of-type{border-left:0}
.bpm__n::before{content:"";position:absolute;inset:0;z-index:-1;
  background:color-mix(in oklab,var(--ink) 4%%,var(--page));
  clip-path:inset(0 0 100%% 0);transition:clip-path var(--spring-mid)}
.bpm__rail{position:absolute;left:0;right:0;top:-1px;height:3px;overflow:hidden}
.bpm__rail::after{content:"";position:absolute;inset:0;background:var(--link);transform:scaleX(0);
  transition:transform var(--spring-fast)}
.bpm__n.is-on::before,.bpm__n:focus-within::before{clip-path:inset(0 0 0 0)}
.bpm__n.is-on .bpm__rail::after,.bpm__n:focus-within .bpm__rail::after{transform:none}
.bpm__n.is-near .bpm__rail::after{transform:scaleX(.4)}
/* its node on the line, numbered in his order; lit, it fills blue */
.bpm__o{position:absolute;left:50%%;top:-39px;z-index:1;box-sizing:border-box;display:grid;
  place-items:center;width:22px;height:22px;margin-left:-11px;border:1.5px solid var(--ink);
  border-radius:50%%;background:var(--page);font:600 12px/1 var(--sans);color:var(--ink);
  font-variant-numeric:tabular-nums;
  transition:background-color var(--t-fast) var(--ease-state),border-color var(--t-quick) var(--ease-state),
    color var(--t-fast) var(--ease-state),transform var(--spring-fast)}
.bpm__o.is-on{background:var(--link);border-color:var(--link);color:var(--page);transform:scale(1.14)}
.bpm__o.is-near{border-color:var(--link);color:var(--link)}
/* THE ORBS (round 15). While a node thinks, its ring gives way to a sphere
   of dots the script draws on a canvas inside it (.bpm__orb), under its
   number: the canvas is the node's own negative layer, over its paper and
   under its text. The number keeps a halo of paper so it reads through the
   dots, and a lit node waits for its orb to settle before it fills. */
.bpm__orb{position:absolute;left:50%%;top:50%%;z-index:-1;width:36px;height:36px;
  margin:-18px 0 0 -18px;pointer-events:none}
.bpm__o.o{border-color:transparent;background-color:var(--page);
  text-shadow:0 0 2px var(--page),0 0 2px var(--page),0 0 1px var(--page)}
.bpm__o.o.is-on{color:var(--link)}
.bpm__top{grid-row:1;display:flex;align-items:flex-start;gap:9px}
.bpm__ic{flex:none;width:24px;height:24px;margin-top:1px;color:var(--ink)}
.bpm__ic svg{display:block;width:24px;height:24px}
/* the home page's icons, their marks in the page's blue: they draw while
   their topic is lit, and nothing that moves here is orange (ROUND15) */
.bpm__ic .i-accent{stroke:var(--link)}
.bpm__h{margin:0;font:600 18px/1.25 var(--serif);letter-spacing:-.006em;color:var(--ink);
  text-wrap:balance}
.bpm__line{grid-row:2;margin:6px 0 0;font:400 13px/1.4 var(--sans);color:var(--muted);
  text-wrap:pretty}
.bpm__docs{grid-row:3;display:grid;align-content:start;gap:22px;margin:18px 0 0;padding:0;
  list-style:none}
.bpm__docs>li{min-width:0;margin:0}
/* the page in preparation: its words quiet */
.bpm__n--soon .bpm__h{color:var(--body)}
.bpm__n--soon .bpm__ic{color:var(--muted)}

/* A CARD: the whole of it opens the document or deck; its picture, cut for
   this box (tools/bp_art.py), multiplied into a quiet plate so a figure's
   white paper is the plate's own; his title; what it holds */
.bpc{display:flex;flex-direction:column;gap:10px;border-radius:var(--r-sm);color:inherit;
  text-decoration:none;-webkit-tap-highlight-color:transparent}
.bpc__art{position:relative;display:block;aspect-ratio:16/9;overflow:hidden;border-radius:var(--r-sm);
  background:var(--surface)}
.bpc__art::after{content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;
  box-shadow:inset 0 0 0 1px color-mix(in oklab,var(--ink) 8%%,transparent)}
.bpc__art img{display:block;width:100%%;height:100%%;object-fit:cover;mix-blend-mode:multiply}
:root[data-theme="dark"] .bpc__art img{mix-blend-mode:normal}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .bpc__art img{mix-blend-mode:normal}}
.bpc__t{font:500 15px/1.34 var(--serif);letter-spacing:-.002em;color:var(--ink);text-wrap:pretty}
.bpc__nb{white-space:nowrap}
.bpc__m{display:flex;align-items:center;gap:7px;margin-top:-3px;font:600 12.5px/1 var(--sans);
  color:var(--muted);font-variant-numeric:tabular-nums}
.bpc__m svg{flex:none;width:15px;height:15px;stroke:currentColor}
.bpc__m .bp__arrow{width:19px;height:19px;margin-left:1px}
/* the page in preparation: an empty plate that says so */
.bpc__art--soon{display:grid;place-items:center;padding:8px;background:none;text-align:center}
.bpc__art--soon::after{box-shadow:inset 0 0 0 1px var(--line)}
.bpc__art--soon .bpc__t{font:italic 500 14.5px/1.3 var(--serif);color:var(--muted)}
.bp__arrow .ar-shaft{stroke-dasharray:13;stroke-dashoffset:9;transition:stroke-dashoffset var(--spring-mid)}
.bp__arrow .ar-head{transition:transform var(--spring-mid) 60ms}
/* A card under the pointer or a key (round 15), one gesture in reading
   order, the card itself never moving:
   - its title's underline (the site's whole-card state, DESIGN_BRIEF 4)
     draws through its lines as a pen would, line after line (a background
     of the inline title, so it runs on from line to line);
   - a hairline of the lit blue opens along the foot of its picture, the
     way the arrow points, the "open" cue;
   - the arrow's shaft draws and its head follows on the spring.
   Leaving, each fades where it stands and folds away only once unseen. */
@property --bpc-u{syntax:"<color>";inherits:false;initial-value:transparent}
.bpc__u{--bpc-u:transparent;background:linear-gradient(var(--bpc-u),var(--bpc-u)) no-repeat 0 100%%/0 1px;
  transition:--bpc-u var(--t-quick) var(--ease-state),background-size 0s var(--t-quick)}
.bpc__art::before{content:"";position:absolute;left:0;right:0;bottom:0;z-index:1;height:2px;
  background:var(--link);transform:scaleX(0);transform-origin:0 50%%;opacity:0;pointer-events:none;
  transition:opacity var(--t-quick) var(--ease-state),transform 0s var(--t-quick)}
@media (hover:hover){
  .bpc:hover .bpc__u{--bpc-u:var(--ink);background-size:100%% 1px;transition:background-size var(--spring-draw)}
  .bpc:hover .bpc__art::before{opacity:1;transform:none;transition:transform var(--spring-draw) 40ms}
  .bpc:hover .ar-shaft,.bpr__a:hover .ar-shaft{stroke-dashoffset:0}
  .bpc:hover .ar-head,.bpr__a:hover .ar-head{transform:translateX(5px)}
  .bpr__a:hover{text-decoration-color:currentColor}
}
.bpc:focus-visible{outline:2px solid var(--focus);outline-offset:4px}
.bpc:focus-visible .bpc__u{--bpc-u:var(--ink);background-size:100%% 1px;transition:none}
.bpc:focus-visible .bpc__art::before{opacity:1;transform:none;transition:none}
.bpc:focus-visible .ar-shaft,.bpr__a:focus-visible .ar-shaft{stroke-dashoffset:0}
/* less motion: the end states at once, the arrow drawn and its head home */
@media (prefers-reduced-motion:reduce){
  .bpc__u,.bpc__art::before{transition:none}
  .bp__arrow .ar-shaft{stroke-dashoffset:0;transition:none}
  .bp__arrow .ar-head{transition:none}
}

/* the drawing over the heads: the line, the ticks down to the columns, and
   the arcs; lit, blue */
.bpm__e{fill:none;stroke:color-mix(in oklab,var(--ink) 22%%,var(--page));stroke-width:1.2;
  stroke-linecap:round;transition:opacity var(--t-mid) var(--ease-state),
    stroke var(--t-fast) var(--ease-state),stroke-width var(--t-fast) var(--ease-state)}
.bpm__e--l{stroke:color-mix(in oklab,var(--ink) 34%%,var(--page));stroke-width:1.5}
.bpm__e--b{stroke:color-mix(in oklab,var(--ink) 40%%,var(--page));stroke-width:1.5}
.bpm__e--s.is-hot{stroke:var(--link);stroke-width:2}
/* a bridge's lit way, drawn from the topic in hand behind its point */
.bpm__lit{fill:none;stroke:var(--link);stroke-width:2;stroke-linecap:round;opacity:0;
  transition:opacity var(--t-fast) var(--ease-state)}
.bpm__lit.is-on{opacity:1}
/* a point that travels a line: a blue point in a soft halo, the last of its
   way lit behind it and fading (its gradient's stops) */
.bpm__pt-t{fill:none;stroke-width:2;stroke-linecap:round}
.bpm__pt-g{fill:var(--link);opacity:.16}
.bpm__pt-c{fill:var(--link)}
.bpm__pt-s0{stop-color:var(--link);stop-opacity:0}
.bpm__pt-s1{stop-color:var(--link);stop-opacity:.9}
.bpm__w{position:absolute;left:0;top:0;padding:1px 7px;border-radius:4px;background:var(--page);
  font:italic 500 14.5px/1.3 var(--serif);color:var(--muted);white-space:nowrap;
  transform:translate(-50%%,-50%%);transition:opacity var(--t-mid) var(--ease-state),
    color var(--t-fast) var(--ease-state)}
.bpm__w.is-hot{color:var(--link)}
/* A word's shimmer, once, as its point passes under it: a thin band of the
   lit blue runs through the word the way the point travels (.is-back, the
   other way). Lit (.is-hot), the band leaves the word blue behind it. The
   script takes the class off when the band has run. */
.bpm__w.is-shim>span{--w0:var(--muted);--w1:var(--muted);color:transparent;
  background:linear-gradient(90deg,var(--w0) 0 45%%,var(--link) 50%%,var(--w1) 55%% 100%%) 100%% 0/300%% 100%%;
  -webkit-background-clip:text;background-clip:text}
.bpm__w.is-run>span{animation:bpm-shim 420ms linear both}
.bpm__w.is-shim.is-hot>span{--w0:var(--link)}
/* in the arrival the band writes the word: ahead of it there is none yet,
   and the word's paper stands at once, over the way the point takes under it */
.bpm__w.is-write{transition:color var(--t-fast) var(--ease-state)}
.bpm__w.is-shim.is-write>span{--w1:transparent}
.bpm__w.is-shim.is-back>span{
  background-image:linear-gradient(270deg,var(--w0) 0 45%%,var(--link) 50%%,var(--w1) 55%% 100%%);
}
.bpm__w.is-run.is-back>span{animation-direction:reverse}
@keyframes bpm-shim{from{background-position:100%% 0}to{background-position:0 0}}
@keyframes bpm-shim-y{from{background-position:0 0}to{background-position:0 100%%}}
/* lit: the topic, its arcs and the topics at their far ends; the rest dims */
.bpm[data-focus] .bpm__n:not(.is-on):not(.is-near):not(.is-link){opacity:.5}
.bpm[data-focus] .bpm__e:not(.is-hot):not(.bpm__e--l),.bpm[data-focus] .bpm__w:not(.is-lit){opacity:.22}

/* HIS RESEARCH, under the five: a brace across all of them, drawn as a
   mathematician's underbrace (two runs that stretch, a point and two ends
   that do not), his sentence at its point, and his research documents as
   cards the size of the topics'. The points that run out from the brace to
   the five are drawn over it (.bpr__pts, the script's). */
.bpr{position:relative;margin:14px 0 0}
.bpr__brace{position:relative;display:flex;height:20px;color:color-mix(in oklab,var(--ink) 45%%,var(--page))}
.bpr__brace svg{display:block;flex:none;height:20px;overflow:visible;fill:none;stroke:currentColor;
  stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
.bpr__end{width:12px}
.bpr__tip{width:28px}
.bpr__brace .bpr__run{flex:1 1 0;min-width:0;width:auto}
.bpr__run--l{transform-origin:100%% 50%%}
.bpr__run--r{transform-origin:0 50%%}
.bpr__brace .bpr__pts{position:absolute;left:0;top:-40px;width:100%%;height:62px;pointer-events:none}
.bpr__h{margin:14px auto 0;max-width:var(--measure);font:600 22px/1.3 var(--serif);
  letter-spacing:-.008em;color:var(--ink);text-align:center;text-wrap:balance}
.bpr__docs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));width:80%%;margin:26px auto 0;
  padding:0;list-style:none}
.bpr__docs>li{min-width:0;margin:0;padding:0 14px}
.bpr__more{margin:22px 0 0;text-align:center}
.bpr__a{display:inline-flex;align-items:center;gap:6px;min-height:44px;font:600 15px/1.2 var(--sans);
  color:var(--link);text-decoration:underline;text-decoration-thickness:1.5px;text-underline-offset:3px;
  text-decoration-color:color-mix(in oklab,currentColor,62%% transparent);
  transition:text-decoration-color var(--t-fast) var(--ease-state)}
.bpr__a .bp__arrow{width:20px;height:20px}
.bpr__a:focus-visible{outline:2px solid var(--focus);outline-offset:2px;border-radius:4px}
.bpm__cap{margin:28px 0 0;max-width:var(--measure);font:500 14px/1.5 var(--sans);color:var(--muted)}

/* upright: the topics one under another on a spine at their left, each
   followed by its cards, the arcs at their right, their words standing on
   the arcs */
@container bpm (width < 920px){
  .bpm__stage{--bpm-mode:tall;grid-template-columns:minmax(0,1fr);grid-template-rows:none;
    row-gap:12px;padding:4px 46px 4px 34px}
  .bpm__stage::before{display:none}
  .bpm__n{grid-row:auto;display:block;border-left:0;padding:14px 12px 18px 16px;
    border-radius:var(--r-md);scroll-margin-top:24px}
  .bpm__n::before{border-radius:inherit;clip-path:inset(0 100%% 0 0 round var(--r-md))}
  .bpm__n.is-on::before,.bpm__n:focus-within::before{clip-path:inset(0 0 0 0 round var(--r-md))}
  .bpm__o{left:-21px;top:14px}
  .bpm__rail{left:5px;right:auto;top:16px;bottom:16px;width:2px;height:auto;border-radius:2px;
    background:color-mix(in oklab,var(--ink) 14%%,var(--page))}
  .bpm__rail::after{transform:scaleY(0)}
  .bpm__n.is-near .bpm__rail::after{transform:scaleY(.45)}
  .bpm__docs{grid-template-columns:repeat(auto-fill,minmax(min(100%%,290px),1fr));gap:14px 22px;
    margin-top:14px}
  .bpc{display:grid;grid-template-columns:min(40%%,150px) minmax(0,1fr);grid-template-rows:auto 1fr;
    column-gap:14px;row-gap:8px;align-items:start}
  .bpc__art{grid-row:span 2}
  .bpc__art--soon{aspect-ratio:auto;min-height:58px}
  .bpc__m{align-self:end;margin-top:0}
  .bpr{margin:26px 46px 0 34px}
  .bpr__docs{width:auto;grid-template-columns:repeat(auto-fill,minmax(min(100%%,290px),1fr));
    gap:14px 22px;margin-top:20px}
  .bpr__docs>li{padding:0}
  .bpm__w{padding:6px 1px;font-size:13px;writing-mode:vertical-rl;
    transform:translate(-50%%,-50%%) rotate(180deg)}
  /* standing, a word reads upward, so its band runs down the page with a
     point that travels down (its own bottom to top, the word turned) */
  .bpm__w.is-shim>span{
    background:linear-gradient(0deg,var(--w0) 0 45%%,var(--link) 50%%,var(--w1) 55%% 100%%) 0 0/100%% 300%%;
    -webkit-background-clip:text;background-clip:text}
  .bpm__w.is-run>span{animation-name:bpm-shim-y}
  .bpm__w.is-shim.is-back>span{
    background-image:linear-gradient(180deg,var(--w0) 0 45%%,var(--link) 50%%,var(--w1) 55%% 100%%)}
}
/* a phone: each card stands upright, its picture the topic's width */
@container bpm (width < 560px){
  .bpm__stage{padding:4px 44px 4px 32px}
  .bpm__o{left:-19px}
  .bpm__n{padding:14px 10px 18px 14px}
  .bpm__docs,.bpr__docs{grid-template-columns:minmax(0,1fr);gap:22px}
  .bpc{display:flex;flex-direction:column;align-items:stretch;gap:10px}
  .bpc__m{align-self:auto;margin-top:-3px}
  .bpr{margin:26px 44px 0 32px}
}

/* Motion, only when it is welcome (round 15, the module's docstring).
   Until the script has laid the table out its topics wait (2s at most, so a
   table whose script never runs still shows). In the arrival each topic
   settles in as the thought reaches its node, whose ring and number wait
   for it (.is-born), and its tick draws down into it; the line and the arcs
   are drawn by the script, behind their points, and each word waits for its
   point (.is-in). The brace opens from its point once it is in view. */
@media (prefers-reduced-motion:no-preference){
  .js .bpm:not(.is-ready) :is(.bpm__n,.bpm__edges,.bpm__words){animation:bpm-hold 2s backwards}
  .bpm.is-intro .bpm__n>:not(.bpm__o):not(.bpm__rail){
    animation:bpm-rise var(--spring-mid) calc(var(--d,0ms) + var(--dd,0ms)) both}
  .bpm__docs{--dd:60ms}
  .bpm.is-intro .bpm__o:not(.is-born){border-color:transparent;background-color:transparent;color:transparent;
    transition:none}
  .bpm.is-intro .bpm__e--s{stroke-dasharray:1 2;animation:bpm-draw var(--spring-slow) var(--d,0ms) both}
  .bpm.is-intro .bpm__w:not(.is-in){opacity:0;transition:none}
  .bpr.is-armed .bpr__tip,.bpr.is-armed .bpr__end{opacity:0}
  .bpr.is-armed .bpr__run{transform:scaleX(0)}
  .bpr.is-draw .bpr__tip{animation:bpr-tip var(--spring-fast) var(--bd,0ms) both}
  .bpr.is-draw .bpr__run{animation:bpr-run var(--spring-slow) calc(var(--bd,0ms) + 70ms) both}
  .bpr.is-draw .bpr__end{animation:bpm-fade var(--t-mid) var(--ease) calc(var(--bd,0ms) + 360ms) both}
}
@keyframes bpm-hold{from,to{opacity:0}}
@keyframes bpm-rise{from{opacity:0;transform:translateY(8px)}}
@keyframes bpm-draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes bpm-fade{from{opacity:0}}
@keyframes bpr-tip{from{opacity:0;transform:translateY(-4px)}}
@keyframes bpr-run{from{transform:scaleX(0)}}
@media (forced-colors:active){
  .bpm__e,.bpr__brace{stroke:CanvasText;color:CanvasText}
  .bpm__e.is-hot{stroke:Highlight}
  .bpm__o{border-color:CanvasText}
  .bpm__o.is-on{forced-color-adjust:none;background:Highlight;border-color:Highlight;color:HighlightText}
  .bpm__n::before{background:Canvas}
  .bpm__orb,.bpm__pt,.bpm__lit,.bpr__pts,.bpc__art::before{display:none}
}

/* the icons draw while their topic is lit, as on the home page */
.bpm .t-run{opacity:0}
@media (prefers-reduced-motion:no-preference){
  .bpm .t-run{stroke-dasharray:1 2;stroke-dashoffset:1;transition:opacity 0s 200ms,stroke-dashoffset 0s 200ms}
  .bpm .t-base{transition:opacity var(--t-fast) var(--ease-state)}
  .bpm .t-win{transition:transform var(--spring-mid)}
  .bpm .t-type{transition:stroke-dashoffset 150ms steps(3,start),opacity 0s 150ms}
  .bpm .t-caret{transition:transform 150ms steps(3,start)}
  .bpm__n.is-on .t-base{opacity:.3}
  .bpm__n.is-on .t-run{opacity:1;stroke-dashoffset:0}
  .bpm__n.is-on .t-in{transition:opacity 0s 40ms,stroke-dashoffset 220ms linear 40ms}
  .bpm__n.is-on .t-out{transition:opacity 0s 260ms,stroke-dashoffset 110ms linear 260ms}
  .bpm__n.is-on .t-fit{transition:opacity 0s 40ms,stroke-dashoffset var(--t-draw) var(--ease-in-out) 40ms}
  .bpm__n.is-on .t-win{transform:translateX(7px);transition:transform var(--t-draw) var(--ease-in-out)}
  .bpm__n.is-on .t-bar{transition:opacity 0s var(--d),stroke-dashoffset var(--spring-fast) var(--d)}
  .bpm__n.is-on .t-bell{transition:opacity 0s 140ms,stroke-dashoffset var(--t-mid) var(--ease-in-out) 140ms}
  .bpm__n.is-on .t-type{transition:opacity 0s,stroke-dashoffset 300ms steps(3,start)}
  .bpm__n.is-on .t-caret{transform:translateX(5.2px);transition:transform 300ms steps(3,start)}
}

@media print{
  .bpm__edges,.bpm__words,.bpm__o,.bpr__brace{display:none}
  .bpm__stage{display:block;padding:0}
  .bpm__stage::before{display:none}
  .bpm__n{display:block;border:0;padding:0;margin:0 0 18px;break-inside:avoid}
  .bpm__docs,.bpr__docs{grid-template-columns:repeat(3,minmax(0,1fr));width:auto;gap:14px}
  .bpm__docs>li,.bpr__docs>li{padding:0;break-inside:avoid}
}
""" % {}

JS = r"""
var fig=document.querySelector('.bpm');
if(fig){
var H=document.documentElement,st=fig.querySelector('.bpm__stage'),svg=fig.querySelector('.bpm__edges'),
  lay=fig.querySelector('.bpm__words'),ns=[].slice.call(fig.querySelectorAll('.bpm__n')),
  os=ns.map(function(n){return n.querySelector('.bpm__o')}),br=fig.querySelector('.bpr'),
  B=JSON.parse(fig.getAttribute('data-bridges')),NS='http://www.w3.org/2000/svg',
  reduce=matchMedia('(prefers-reduced-motion: reduce)'),forced=matchMedia('(forced-colors: active)'),
  byId={},edges=[],cur=null,pin=null,played=false,tm=0,ta=0,tI=0,size='',up=false,hashed=0,
  runs=[],orbs=[],todo=[],woke=[],raf=0,last=0,intro1=0,INK='',LINK='',Q=[0,0],gid=0,lastB=-1e4,io2=null,
  /* the thought (ms): it sets out from the first topic, runs the line, and
     the bridges set out as it nears the fifth */
  DEP=90,TL=720,GL=.24,ARC=.8,ARCG=100,HOLD=130,TAIL=36,RISE=20,RT=220,
  /* an orb, the column's own (parts/bpnav.py) at the node's size: N dots on
     a sphere that grows from the ring (R0, the ring's middle) to R1, turning
     at SPIN times its excitation cubed; a core under the number keeps it
     clear. Springs critically damped: WAKE out, REST back. */
  N=96,SX=[],SY=[],SZ=[],OC=36,R0=10.25,R1=14,CORE=6.5,
  WAKE=2*Math.PI/.24,REST=2*Math.PI/.42,SPIN=2*Math.PI/1.6,
  SLOW=/*SLOW*/[],SLOWT=/*SLOWT*/800;
ns.forEach(function(n,k){byId[n.id]=n;n._k=k});
for(var i=0;i<N;i++){var y0=1-2*(i+.5)/N,r0=Math.sqrt(1-y0*y0),a0=i*2.399963;
  SX[i]=Math.cos(a0)*r0;SY[i]=y0;SZ[i]=Math.sin(a0)*r0}
function mk(tag,cls){var e=document.createElementNS(NS,tag);if(cls)e.setAttribute('class',cls);return e}
/* where an element stands in the stage; a node's centre holds while it is scaled */
function box(el){var r=el.getBoundingClientRect(),s=st.getBoundingClientRect(),k=s.width/st.clientWidth||1,
  x=(r.left-s.left)/k,y=(r.top-s.top)/k,w=r.width/k,h=r.height/k;
  return {x:x,y:y,w:w,h:h,cx:x+w/2,cy:y+h/2}}
function f(v){return Math.round(v*10)/10}
/* motion is welcome, and colours are the page's own */
function live(){return !reduce.matches&&!forced.matches}
function tokens(){var s=getComputedStyle(H);INK=s.getPropertyValue('--ink').trim();LINK=s.getPropertyValue('--link').trim()}
/* a word at its arc's crest, never past the stage's edge over the line;
   upright, its arc's crest is in the stage's margin and so is the word */
function place(w,pt){var hw=w.offsetWidth/2+2,hh=w.offsetHeight/2+2,W=up?1/0:st.clientWidth,q=pt();
  w.style.left=f(Math.max(hw,Math.min(W-hw,q[0])))+'px';w.style.top=f(Math.max(hh,q[1]))+'px'}
/* a line of the drawing, from its points: a line's two ends, or a curve's
   four (a cubic's ends and controls). An arc carries its word, and keeps the
   same curve the other way round (rd), for a point that sets out from its
   far end. */
function path(c){var d='M'+f(c[0])+' '+f(c[1]);
  return d+(c.length>4?'C'+f(c[2])+' '+f(c[3])+' '+f(c[4])+' '+f(c[5])+' '+f(c[6])+' '+f(c[7]):'L'+f(c[2])+' '+f(c[3]))}
function edge(kind,a,b,c,pt,word){
  var p=mk('path','bpm__e bpm__e--'+kind),d=path(c),r=[];p.setAttribute('d',d);p.setAttribute('pathLength','1');
  svg.appendChild(p);for(var j=c.length-2;j>=0;j-=2)r.push(c[j],c[j+1]);
  var e={kind:kind,a:a,b:b,el:p,c:c,d:d,rd:path(r),w:null,h:null,P:null};
  if(word){var w=document.createElement('span'),t=document.createElement('span');w.className='bpm__w';
    t.textContent=word;w.appendChild(t);lay.appendChild(w);place(w,pt);e.w=w}
  edges.push(e);return e}
function tall(){return getComputedStyle(st).getPropertyValue('--bpm-mode').trim()==='tall'}
function layout(){
  var W=st.clientWidth,H2=st.clientHeight;if(!W)return;
  hush();
  svg.setAttribute('viewBox','0 0 '+W+' '+H2);svg.textContent='';lay.textContent='';edges=[];
  up=tall();var bx=ns.map(box),o=os.map(box),r=os[0].offsetWidth/2,at={},L=ns.length-1;
  ns.forEach(function(n,k){at[n.id]=o[k]});
  if(!up){
    /* the line through the nodes, a tick from each node down to its column,
       and the arcs over the nodes, higher the further they reach; an arc
       leaves its node's rim leaning toward the node it goes to, a near one
       more than a far one, so arcs that share a node fan out from it */
    var y=o[0].cy,top=bx[0].y;
    edge('l','line','line',[o[0].cx,y,o[L].cx,y]);
    ns.forEach(function(n,k){edge('s','hub',n.id,[o[k].cx,y+r+2,o[k].cx,top])});
    B.forEach(function(q){var A=byId[q[1]],Z=byId[q[2]];if(!A||!Z)return;
      var a=at[q[1]].cx,z=at[q[2]].cx,span=Math.abs(A._k-Z._k),g=(span>1?10:44)*Math.PI/180,
        sx=Math.sin(g),cy=Math.cos(g),R=r+1.5,h=30+26*(span-1),y0=y-r-2,
        c=(y0-h-(y-R*cy))/(-.75*cy),ye=y-R*cy;
      edge('b',q[1],q[2],[a+R*sx,ye,a+R*sx+c*sx,ye-c*cy,z-R*sx-c*sx,ye-c*cy,z-R*sx,ye],
        function(){return [(a+z)/2,y0-h]},q[0])});
  }else{
    /* the spine through the nodes, and the arcs out at the right */
    var xr=0;bx.forEach(function(b){xr=Math.max(xr,b.x+b.w)});
    edge('l','line','line',[o[0].cx,o[0].cy,o[L].cx,o[L].cy]);
    B.forEach(function(q){var A=byId[q[1]],Z=byId[q[2]];if(!A||!Z)return;
      var ya=at[q[1]].cy,yz=at[q[2]].cy,w=24+26*(Math.abs(A._k-Z._k)-1),x0=xr+4,x1=xr+4+w;
      edge('b',q[1],q[2],[x0,ya,x1,ya,x1,yz,x0,yz],function(){return [x0+.75*w,(ya+yz)/2]},q[0])});
  }
  /* over each arc, its lit way: drawn from the topic in hand toward the one
     it reaches, behind the point that carries it (.bpm__lit) */
  edges.forEach(function(e){if(e.kind!=='b')return;var h=mk('path','bpm__lit');h.setAttribute('pathLength','1');
    h.setAttribute('d',e.d);svg.appendChild(h);e.h=h});
  if(played&&up)watch();
  return true}

/* ---------------------------------------------------------------------------
   THE THOUGHT AND THE ORBS (round 15; the module's docstring). One clock for
   all that moves: points that travel the lines (runs), the nodes' orbs, and
   things set for a moment (todo). Frames are asked for only while something
   moves; at rest there are none. */
/* easing in and out over a at each end, even between (the column's glide) */
function gl(a){var k=1/(1-a);return function(u){return u<a?k*u*u/(2*a):u>1-a?1-k*(1-u)*(1-u)/(2*a):k*(u-a/2)}}
/* when an eased run is at share q of its way */
function inv(e,q){var lo=0,hi=1,m,j;for(j=0;j<24;j++){m=(lo+hi)/2;if(e(m)<q)lo=m;else hi=m}return (lo+hi)/2}
/* the brace's runs open on the site's slow spring (--spring-slow, the same
   stops), so its points can ride their ends */
function slow(t){var n=SLOW.length-1,u,j;if(t<=0)return 0;u=t/SLOWT*n;j=Math.floor(u);
  return j>=n?1:SLOW[j]+(SLOW[j+1]-SLOW[j])*(u-j)}
function unslow(q){var n=SLOW.length-1,j;for(j=1;j<=n;j++)if(SLOW[j]>=q)
  return SLOWT*(j-1+(q-SLOW[j-1])/((SLOW[j]-SLOW[j-1])||1))/n;return SLOWT}
/* a way to travel: points x,y, their distances along it, and its length */
function way(X,Y){var D=[0],j;for(j=1;j<X.length;j++)
  D.push(D[j-1]+Math.sqrt((X[j]-X[j-1])*(X[j]-X[j-1])+(Y[j]-Y[j-1])*(Y[j]-Y[j-1])));
  return {X:X,Y:Y,D:D,L:D[D.length-1]}}
/* a line's way, or a curve's, sampled from its own points (40 steps of the
   cubic; the way's distances make the point's pace even along it) */
function poly(c){var X=[],Y=[],j,t,u,n=c.length>4?40:1;
  if(n===1)return way([c[0],c[2]],[c[1],c[3]]);
  for(j=0;j<=n;j++){t=j/n;u=1-t;
    X.push(u*u*u*c[0]+3*u*u*t*c[2]+3*u*t*t*c[4]+t*t*t*c[6]);Y.push(u*u*u*c[1]+3*u*u*t*c[3]+3*u*t*t*c[5]+t*t*t*c[7])}
  return way(X,Y)}
function flip(P){return way(P.X.slice().reverse(),P.Y.slice().reverse())}
function samp(e){return e.P||(e.P=poly(e.c))}
/* the point s along a way, into Q */
function at(P,s){var D=P.D,lo=0,hi=D.length-1,m,u;
  if(s<=0){Q[0]=P.X[0];Q[1]=P.Y[0];return}
  if(s>=P.L){Q[0]=P.X[hi];Q[1]=P.Y[hi];return}
  while(hi-lo>1){m=(lo+hi)>>1;if(D[m]<s)lo=m;else hi=m}
  u=(s-D[lo])/((D[hi]-D[lo])||1);Q[0]=P.X[lo]+(P.X[hi]-P.X[lo])*u;Q[1]=P.Y[lo]+(P.Y[hi]-P.Y[lo])*u}
/* a point: the blue of the page's links, in a soft halo, with the last 36px
   of its way behind it lit and fading (a stroke of its way, dashed to that
   stretch, under a gradient laid along it) */
function point(sv,P){
  var g=mk('g','bpm__pt'),t=mk('path','bpm__pt-t'),h=mk('g'),c=mk('circle','bpm__pt-g'),c2=mk('circle','bpm__pt-c'),
    lg=mk('linearGradient'),s0=mk('stop','bpm__pt-s0'),s1=mk('stop','bpm__pt-s1'),df=sv.querySelector('defs'),
    id='bpm-t'+(++gid),d='',j;
  if(!df)df=sv.insertBefore(mk('defs'),sv.firstChild);
  lg.setAttribute('id',id);lg.setAttribute('gradientUnits','userSpaceOnUse');
  s0.setAttribute('offset','0');s1.setAttribute('offset','1');lg.appendChild(s0);lg.appendChild(s1);df.appendChild(lg);
  for(j=0;j<P.X.length;j++)d+=(j?'L':'M')+f(P.X[j])+' '+f(P.Y[j]);
  t.setAttribute('d',d);t.setAttribute('stroke','url(#'+id+')');
  c.setAttribute('r','4.6');c2.setAttribute('r','2.2');h.appendChild(c);h.appendChild(c2);
  g.appendChild(t);g.appendChild(h);g.style.opacity='0';sv.appendChild(g);
  return {g:g,t:t,h:h,lg:lg}}
function put(o,P,s,a){
  var x,y,s0=s>TAIL?s-TAIL:0;at(P,s);x=Q[0];y=Q[1];
  o.h.setAttribute('transform','translate('+f(x)+' '+f(y)+')');
  at(P,s0);
  o.lg.setAttribute('x1',f(Q[0]));o.lg.setAttribute('y1',f(Q[1]));o.lg.setAttribute('x2',f(x));o.lg.setAttribute('y2',f(y));
  o.t.style.strokeDasharray=f(s-s0)+' '+Math.ceil(P.L+2);o.t.style.strokeDashoffset=f(-s0);
  o.g.style.opacity=a.toFixed(3)}
function unpoint(o){if(!o)return;if(o.g.parentNode)o.g.parentNode.removeChild(o.g);
  if(o.lg.parentNode)o.lg.parentNode.removeChild(o.lg)}
/* a point's errand: along way P from t0, at pos(t) (its easing over dur
   unless it says), drawing `draw` behind it (a path of pathLength 1) where
   there is one. Its marks happen as it passes a distance, its end as it
   arrives; each has a quiet form (q), for a motion cut short, that leaves
   what it would have left and moves nothing. */
function go(o){
  if(!o.pos){var e=o.ease||gl(.3),L=o.P.L,d=o.dur;o.pos=function(t){return L*e(t<d?t/d:1)}}
  o.pt=point(o.svg,o.P);o.marks=o.marks||[];runs.push(o);kick();return o}
function step(r,now){
  var t=now-r.t0,s,a,j,m;
  if(t<0){r.pt.g.style.opacity='0';return 1}
  s=r.pos(t);if(s>r.P.L)s=r.P.L;
  if(r.draw&&!r.kill)r.draw.style.strokeDashoffset=s>0?(1-s/r.P.L).toFixed(4):'1';
  for(j=0;j<r.marks.length;j++){m=r.marks[j];if(!m.done&&s>=m.s){m.done=1;if(!r.kill)m.fn(now,r)}}
  if(r.word)band(r,s);
  if(t>=r.dur&&!r.fin){r.fin=1;if(r.end&&!r.kill)r.end(now)}
  a=r.alpha?r.alpha(t):t<80?t/80:t>r.dur?1-(t-r.dur)/150:1;
  if(r.kill)a=Math.min(a,1-(now-r.kill)/120);
  if(a<0)a=0;put(r.pt,r.P,s,a);
  return a>0||t<r.dur}
function finish(r){var j,m;
  if(r.word)unband(r);
  for(j=0;j<r.marks.length;j++){m=r.marks[j];if(!m.done){m.done=1;if(m.q&&!r.kill)m.q()}}
  if(!r.fin){r.fin=1;if(r.end&&!r.kill)r.end(0,1)}
  if(r.draw&&!r.kill)r.draw.style.strokeDashoffset='0';
  unpoint(r.pt)}
/* a node's orb, made the first time it thinks: a canvas inside the node,
   under its number (the stylesheet), at the device's ratio, 2 at most */
function orb(k){var q=orbs[k];if(q)return q;
  var cv=document.createElement('canvas'),g=cv.getContext&&cv.getContext('2d'),d;if(!g)return null;
  d=Math.min(2,window.devicePixelRatio||1);cv.className='bpm__orb';cv.width=cv.height=Math.round(OC*d);
  os[k].appendChild(cv);
  return orbs[k]={el:os[k],cv:cv,g:g,d:d,E:0,EV:0,ET:0,EW:WAKE,EH:0,AN:k*1.9,o:0,on:0,col:INK}}
/* a topic thinks: its orb wakes (to e), holds, and settles back into the
   ring; the ring gives way to it meanwhile (.o) */
function wake(k,e,hold,now,col){if(!live())return;var q=orb(k);if(!q)return;
  if(q.ET<e){q.ET=e;q.EW=WAKE}q.EH=Math.max(q.EH,now+hold);q.col=col||INK;
  if(!q.o){q.o=1;q.el.classList.add('o')}kick()}
function spin(q,dt,now){var d,c,x,busy=0;
  if(q.ET&&now>=q.EH){q.ET=0;q.EW=REST}
  d=q.E-q.ET;
  if(d||q.EV){c=q.EV+q.EW*d;x=Math.exp(-q.EW*dt);q.E=q.ET+(d+c*dt)*x;q.EV=(q.EV-q.EW*c*dt)*x;
    if(Math.abs(q.E-q.ET)<.002&&Math.abs(q.EV)<.02){q.E=q.ET;q.EV=0}busy=1}
  if(q.ET)busy=1;
  if(q.o&&!q.ET&&q.E<.35){q.o=0;q.el.classList.remove('o')}
  q.AN+=dt*SPIN*q.E*q.E*q.E;
  paint(q);return busy}
/* the orb: its dots on a sphere turned by AN and tilted 22 degrees toward
   the reader, the nearer the brighter and larger. Waking, the dots leave the
   ring's line for the sphere; settling, they go back to it (m), so the orb
   grows out of the ring and ends on it. Dots over the number are faint, and
   those behind it are not drawn. */
function paint(q){var g=q.g,e=q.E,j,px,pz,py,z,t,rh,al,s,m,r,ca,sa,C=OC/2,A,k;
  g.setTransform(1,0,0,1,0,0);g.clearRect(0,0,q.cv.width,q.cv.height);
  if(e<=.001){q.on=0;return}
  q.on=1;g.setTransform(q.d,0,0,q.d,0,0);g.fillStyle=q.col;
  s=e*e*(3-2*e);m=1-s;r=R0+(R1-R0)*s;ca=Math.cos(q.AN);sa=Math.sin(q.AN);A=e<.3?e/.3:1;k=CORE/r;
  for(j=0;j<N;j++){
    px=SX[j]*ca+SZ[j]*sa;pz=SZ[j]*ca-SX[j]*sa;
    py=SY[j]*.93-pz*.37;z=SY[j]*.37+pz*.93;
    rh=Math.sqrt(px*px+py*py)||1;px+=(px/rh-px)*m;py+=(py/rh-py)*m;
    t=(z+1)/2;al=A*(s*(.16+.84*t*t)+.62*m);
    if(px*px+py*py<k*k){if(z<0)continue;al*=.3}
    g.globalAlpha=al>1?1:al;g.beginPath();g.arc(C+px*r,C+py*r,.3+.38*t*s+.28*m,0,6.2832);g.fill()}
  g.globalAlpha=1}
/* something set for a moment, on the same clock */
function when(t,fn){todo.push({t:t,fn:fn});kick()}
function frame(now){
  var dt=last?(now-last)/1e3:1/60,busy=0,j,q;raf=0;last=now;if(dt>.1)dt=.1;
  for(j=0;j<todo.length;j++)if(now>=todo[j].t){q=todo.splice(j--,1)[0];q.fn(now)}
  if(todo.length)busy=1;
  for(j=runs.length-1;j>=0;j--)if(step(runs[j],now))busy=1;else{unpoint(runs[j].pt);runs.splice(j,1)}
  for(j=0;j<orbs.length;j++){q=orbs[j];if(q&&(q.ET||q.E||q.EV||q.on)&&spin(q,dt,now))busy=1}
  if(busy)raf=requestAnimationFrame(frame);else last=0}
function kick(){if(!raf)raf=requestAnimationFrame(frame)}
/* everything to where it would have come, at once: the tab hidden, the
   figure scrolled away, the page laid out again, less motion asked for */
function hush(){var j,q,t=todo;todo=[];
  for(j=0;j<t.length;j++)t[j].fn(0,1);
  for(j=0;j<runs.length;j++)finish(runs[j]);runs=[];
  for(j=0;j<orbs.length;j++){q=orbs[j];if(!q)continue;q.E=q.ET=q.EV=q.EH=0;paint(q);
    if(q.o){q.o=0;q.el.classList.remove('o')}}
  [].forEach.call(lay.querySelectorAll('.is-shim'),function(w){w.classList.remove('is-shim','is-run','is-back','is-write')});
  if(intro1)endIntro();
  if(raf)cancelAnimationFrame(raf);raf=0;last=0}
/* A word's shimmer, once: a thin band of blue runs through it the way its
   point travels (back: the other way), and a lit word (hot) is left blue
   behind it. As a word comes into view (upright) the band runs by itself
   (.is-run); on a bridge it runs with the point, which passes under the
   word: the band is where the point is, from half the word's length before
   it to half after, so the word lights where the thought goes through it. */
function shim(w,back,hot){w.classList.add('is-in');if(hot)w.classList.add('is-hot');
  if(!live())return;w.classList.remove('is-shim','is-run');w.classList.toggle('is-back',!!back);
  void w.offsetWidth;w.classList.add('is-shim','is-run')}
lay.addEventListener('animationend',function(e){var w=e.target.parentNode;
  if(w&&w.classList)w.classList.remove('is-shim','is-run','is-back')});
function mark(w,P,back,hot,write){var sp=w.firstChild,n=up?sp.offsetHeight:sp.offsetWidth;
  return {s:Math.max(0,P.L/2-n),fn:function(now,r){if(hot)w.classList.add('is-hot');
      w.classList.remove('is-run');w.classList.toggle('is-back',!!back);w.classList.toggle('is-write',!!write);
      w.classList.add('is-shim','is-in');
      r.word={w:w,sp:sp,s0:P.L/2-n,n:2*n,flip:!back!==!up,y:up}},
    q:function(){w.classList.add('is-in');if(hot)w.classList.add('is-hot')}}}
function band(r,s){var o=r.word,u=(s-o.s0)/o.n;if(u>=1||r.kill){unband(r);return}
  u=o.flip?u:1-u;u=(u<0?0:u*100).toFixed(1)+'%';
  o.sp.style.backgroundPosition=o.y?'0 '+u:u+' 0'}
function unband(r){var o=r.word;r.word=null;o.sp.style.backgroundPosition='';
  o.w.classList.remove('is-shim','is-back','is-write')}
function born(k,now,q){os[k].classList.add('is-born');if(!q)wake(k,1,HOLD,now,INK)}

/* THE ARRIVAL. As the page opens, with the line on screen: the thought sets
   out from the first topic and runs the line to the fifth, drawing it; each
   node is born as it arrives, thinks, and rests as its numbered ring, and
   its topic settles in under it. Near the fifth, a point sets out along each
   bridge from its first topic to its second, drawing it, and the word at its
   crest shimmers as the point passes under it. Then the brace, when it is in
   view. About 1.5s, then rest. Upright (a phone), the topics simply settle
   in, and each node thinks as it comes into view. */
function intro(){
  if(played)return;played=true;
  var r=st.getBoundingClientRect(),bt=parseFloat(getComputedStyle(st).paddingTop)||0;
  if(!edges.length||!live()||document.hidden||performance.now()>2600||
    (up?r.top>innerHeight*.9:r.top+bt<0||r.top+bt>innerHeight*.92)){still();return}
  /* it starts with a frame, so the stylesheet's part of it (the topics, the
     ticks) and the script's (the points, the orbs) keep one time */
  var asked=performance.now();
  requestAnimationFrame(function(now){
    if(now-asked>400||document.hidden){still();return}
    play(now)})}
/* no arrival: the table as it stands, and a topic the address names lit;
   the brace still opens once it comes into view */
function still(){fig.classList.add('is-ready');if(up)watch();brace(0);if(hashed){hashed=0;arrive()}}
function play(now){
  tokens();intro1=1;
  var o=os.map(box),ln=null,xs=[],tk=[],k,P,g=gl(GL),t0,end=0,j=0;
  if(up){
    ns.forEach(function(n,k){n.style.setProperty('--d',(40+70*k)+'ms')});
    os.forEach(function(x){x.classList.add('is-born')});
    edges.forEach(function(e){if(e.w)e.w.classList.add('is-in')});
    fig.classList.add('is-ready','is-intro');watch();brace(0);
    tI=setTimeout(endIntro,1200);return}
  edges.forEach(function(e){if(e.kind==='l')ln=e});
  P=samp(ln);
  for(k=0;k<ns.length;k++){xs[k]=Math.abs(o[k].cx-o[0].cx);tk[k]=k?DEP+inv(g,xs[k]/P.L)*TL:0}
  ns.forEach(function(n,k){n.style.setProperty('--d',Math.round(tk[k]+30)+'ms')});
  edges.forEach(function(e){if(e.kind==='s')e.el.style.setProperty('--d',Math.round(tk[byId[e.b]._k]+20)+'ms');
    else{e.el.style.strokeDasharray='1 2';e.el.style.strokeDashoffset='1'}});
  fig.classList.add('is-ready','is-intro');
  born(0,now);
  go({P:P,t0:now+DEP,dur:TL,ease:g,draw:ln.el,svg:svg,marks:xs.slice(1).map(function(x,j){
    return {s:x-3,fn:function(t){born(j+1,t)},q:function(){born(j+1,0,1)}}})});
  t0=now+DEP+TL*ARC;
  edges.forEach(function(e){if(e.kind!=='b')return;
    var Pb=samp(e),d=Math.round(Math.max(400,Math.min(620,280+.5*Pb.L))),t=t0+ARCG*j++;end=Math.max(end,t+d);
    go({P:Pb,t0:t,dur:d,ease:gl(.3),draw:e.el,svg:svg,marks:e.w?[mark(e.w,Pb,0,0,1)]:[]})});
  brace(end-120);
  tI=setTimeout(endIntro,Math.max(end-now+200,tk[ns.length-1]+900))}
function endIntro(){intro1=0;clearTimeout(tI);fig.classList.remove('is-intro');
  os.forEach(function(x){x.classList.add('is-born')});
  edges.forEach(function(e){e.el.style.strokeDasharray=e.el.style.strokeDashoffset='';if(e.w)e.w.classList.add('is-in')});
  if(hashed){hashed=0;arrive()}}
/* upright: each node thinks once as it comes into view, one after another
   when several come at once, and each word shimmers once as it does, the
   way it reads (up the page: .is-back) */
function watch(){if(!window.IntersectionObserver||!live())return;if(io2)io2.disconnect();
  var q=0;
  io2=new IntersectionObserver(function(es){var now=performance.now();
    es.forEach(function(x){if(!x.isIntersecting||!up)return;var el=x.target,k=os.indexOf(el);io2.unobserve(el);
      if(k>=0){if(woke[k])return;woke[k]=1}
      q=Math.max(now,q+170);
      when(q,function(t,quiet){if(quiet||!up)return;tokens();if(k>=0)wake(k,1,HOLD,t,INK);else shim(el,1,0)})})},
    {rootMargin:'0px 0px -14% 0px'});
  os.forEach(function(x,k){if(!woke[k])io2.observe(x)});
  edges.forEach(function(e){if(e.w)io2.observe(e.w)})}

/* HIS RESEARCH: the brace under the five draws itself from its point once
   it is in view (at the end of the arrival if it is already on screen), and
   a point runs out from its point to each of the five, "involves all of
   these": along the brace on the ends of its opening runs, then up into its
   column. Pointing at one of his research documents runs them again. */
function brace(at){
  if(!br||!window.IntersectionObserver)return;
  if(!live())return;
  br.classList.add('is-armed');
  var io=new IntersectionObserver(function(es){if(!es[0].isIntersecting)return;io.disconnect();
    when(Math.max(performance.now(),at||0),bdraw)},{rootMargin:'0px 0px -10% 0px'});
  io.observe(br)}
function bdraw(now,quiet){br.classList.remove('is-armed');
  if(quiet||!live())return;
  br.style.setProperty('--bd','0ms');br.classList.add('is-draw');
  if(!up){tokens();bpoints(now,0)}}
function bpoints(now,again){
  var bw=br.querySelector('.bpr__brace'),tip=bw&&bw.querySelector('.bpr__tip'),end=bw&&bw.querySelector('.bpr__end');
  if(!tip||!end)return;
  var sv=bw.querySelector('.bpr__pts');
  if(!sv){sv=mk('svg','bpr__pts');sv.setAttribute('aria-hidden','true');sv.setAttribute('focusable','false');bw.appendChild(sv)}
  /* where the brace's point is, and how long a run is (from its end to its
     point), in the brace's own box: its parts are <svg>s, which have no
     offsets, and the runs are scaled while they open */
  var W=bw.clientWidth,b=bw.getBoundingClientRect(),z=W/(b.width||W),tb=tip.getBoundingClientRect(),
    x0=(tb.left-b.left)*z,x1=(tb.right-b.left)*z,cx=(x0+x1)/2,len=x0-(end.getBoundingClientRect().right-b.left)*z,
    Y=50,Y1=Y-RISE,t0=now+(again?0:70);
  sv.setAttribute('viewBox','0 0 '+W+' 62');
  ns.forEach(function(n){var c=n.getBoundingClientRect(),x=f(((c.left+c.right)/2-b.left)*z),side,xs,dx,tk,P,C=5;
    if(Math.abs(x-cx)<x1-cx){   /* through the brace's point, straight up */
      P=way([cx,cx],[59,Y1]);
      go({P:P,t0:now,dur:300,brace:1,svg:sv,pos:function(t){var u=t<300?t/300:1;return P.L*(1-(1-u)*(1-u)*(1-u))},
        alpha:function(t){return t<60?t/60:t<120?1:Math.max(0,1-(t-120)/180)}});return}
    side=x<cx?-1:1;xs=side<0?x0:x1;dx=Math.abs(x-xs)-C;
    P=way([xs,x-side*C,x-side*C*.29,x,x],[Y,Y,Y-C*.29,Y-C,Y1]);
    tk=unslow(Math.min(1,dx/len));
    go({P:P,t0:t0,dur:tk+RT,brace:1,svg:sv,
      pos:function(t){if(t<tk)return Math.min(dx,len*slow(t));var u=(t-tk)/RT;u=u>1?1:u;return dx+(P.L-dx)*(1-(1-u)*(1-u))},
      alpha:function(t){return t<50?t/50:t<tk+RT*.35?1:Math.max(0,1-(t-tk-RT*.35)/(RT*.65))}})})}
function again(){var now=performance.now();
  if(!br||!live()||up||intro1||now-lastB<2500||br.classList.contains('is-armed'))return;
  for(var j=0;j<runs.length;j++)if(runs[j].brace)return;
  lastB=now;tokens();bpoints(now,1)}
if(br)[].forEach.call(br.querySelectorAll('.bpc'),function(a){
  a.addEventListener('pointerenter',function(e){if(e.pointerType==='mouse')again()});
  a.addEventListener('focus',function(){if(a.matches&&a.matches(':focus-visible'))again()})});

/* A TOPIC IN HAND (pointed at, tabbed into, tapped, or arrived at from a
   link): its column fills and its rule draws; its node's orb wakes and
   settles into the lit node; from it a point runs along each bridge it
   shares, lighting the way behind it and the word it passes, and each topic
   at a far end thinks a moment as its point arrives and stays lit. The rest
   dims. Once, then still while it stays in hand; less motion asked for, or
   laid out again (rest), the lit state comes at once. */
function focus(id,rest){if(cur===id)return;cur=id;fig.setAttribute('data-focus',id);calm();
  var now=performance.now(),m=!rest&&live()&&!intro1,near={};
  if(m)tokens();
  edges.forEach(function(e){
    var h=e.kind!=='l'&&(e.a===id||e.b===id),back,far,P,d;e.el.classList.toggle('is-hot',h);
    if(e.w){e.w.classList.remove('is-hot','is-shim','is-run','is-back','is-write');e.w.firstChild.style.backgroundPosition='';
      e.w.classList.toggle('is-lit',h)}
    if(!e.h)return;e.h.classList.toggle('is-on',h);
    if(!h)return;
    back=e.b===id;far=back?e.a:e.b;near[far]=1;e.h.setAttribute('d',back?e.rd:e.d);
    if(!m){e.h.style.strokeDasharray=e.h.style.strokeDashoffset='';if(e.w)e.w.classList.add('is-hot');return}
    e.h.style.strokeDasharray='1 2';e.h.style.strokeDashoffset='1';
    P=back?flip(samp(e)):samp(e);d=Math.round(Math.max(380,Math.min(620,260+.5*P.L)));
    go({P:P,t0:now+50,dur:d,ease:gl(.3),draw:e.h,svg:svg,hover:1,marks:e.w?[mark(e.w,P,back,1)]:[],
      end:function(t,q){reach(far,t,q)}})});
  ns.forEach(function(n,k){var on=n.id===id;n.classList.toggle('is-on',on);n.classList.toggle('is-link',!!near[n.id]);
    n.classList.remove('is-near');os[k].classList.toggle('is-on',on);os[k].classList.remove('is-near')});
  if(m)wake(byId[id]._k,1,160,now,LINK);else for(var x in near)reach(x,0,1)}
/* a far topic, reached */
function reach(id,t,q){var n=byId[id];if(!n||!cur)return;n.classList.add('is-near');os[n._k].classList.add('is-near');
  if(!q)wake(n._k,.75,40,t,LINK)}
/* the points of the topic last in hand fade where they are */
function calm(){var now=performance.now();runs.forEach(function(r){if(r.hover&&!r.kill)r.kill=now})}
function blur(){cur=null;fig.removeAttribute('data-focus');calm();
  edges.forEach(function(e){e.el.classList.remove('is-hot');if(e.w)e.w.classList.remove('is-hot','is-lit');
    if(e.h)e.h.classList.remove('is-on')});
  ns.concat(os).forEach(function(n){n.classList.remove('is-on','is-near','is-link')})}
ns.forEach(function(n){
  n.addEventListener('pointerenter',function(e){if(e.pointerType==='mouse'){clearTimeout(tm);focus(n.id)}});
  n.addEventListener('pointerleave',function(e){if(e.pointerType!=='mouse'||pin)return;
    tm=setTimeout(function(){if(!n.contains(document.activeElement))blur()},90)});
  n.addEventListener('focusin',function(){clearTimeout(tm);focus(n.id)});
  n.addEventListener('focusout',function(e){if(!pin&&!n.contains(e.relatedTarget))tm=setTimeout(blur,0)});
  /* a tap on a topic, not on its cards, lights it until the next tap */
  n.addEventListener('click',function(e){if(e.target.closest('a'))return;
    pin=pin===n.id?null:n.id;if(pin)focus(pin);else blur()})});
document.addEventListener('pointerdown',function(e){
  if(pin&&!(e.target.closest&&e.target.closest('.bpm__n'))){pin=null;blur()}});
/* arriving at a topic from elsewhere: its column comes into view under the
   line (its scroll margin keeps the line in sight) and stays lit a moment */
function arrive(){var n=byId[decodeURIComponent(location.hash.slice(1))];if(!n)return;
  n.scrollIntoView({block:'start',behavior:reduce.matches?'auto':'smooth'});
  clearTimeout(ta);pin=n.id;focus(n.id);
  ta=setTimeout(function(){if(pin===n.id){pin=null;blur()}},3600)}
addEventListener('hashchange',arrive);
var queued=0;
function redo(){queued=0;var now=st.clientWidth+'x'+st.clientHeight;
  if(now===size&&edges.length)return;size=now;
  var id=cur;if(!layout())return;
  if(id){cur=null;focus(id,1)}}
function later(){if(!queued)queued=requestAnimationFrame(redo)}
if(window.ResizeObserver)new ResizeObserver(later).observe(st);addEventListener('resize',later);
/* nothing moves where it cannot be seen: the tab hidden, the figure off
   screen, the page put away, or less motion asked for */
document.addEventListener('visibilitychange',function(){if(document.hidden)hush()});
addEventListener('pagehide',hush);
if(window.IntersectionObserver)new IntersectionObserver(function(es){
  if(!es[0].isIntersecting&&(runs.length||todo.length||intro1))hush()}).observe(fig);
if(reduce.addEventListener)reduce.addEventListener('change',function(){if(!reduce.matches)return;
  hush();if(br)br.classList.remove('is-armed')});
(document.fonts&&document.fonts.ready?document.fonts.ready:Promise.resolve()).then(function(){
  redo();if(location.hash)hashed=1;intro()})}
"""


def _spring(name):
    """(settle ms, stops) of one of the site's springs (parts/springs.py, the
    curve theme.py writes into --spring-<name>), or None without it."""
    try:
        from parts.springs import SPRINGS
    except ImportError:
        return None
    _, settle, easing = SPRINGS[name]
    return settle, [float(v) for v in re.findall(r"-?\d*\.?\d+", easing.split("(", 1)[1])]


# The brace's points ride the ends of its runs, which open on --spring-slow:
# the script samples the same stops, or a straight run where there are none.
_SLOW = _spring("slow") or (800, [0.0, 1.0])
JS = (JS.replace("/*SLOWT*/800", str(_SLOW[0]))
      .replace("/*SLOW*/[]", json.dumps(_SLOW[1], separators=(",", ":"))))

ARROW = ('<svg class="bp__arrow" viewBox="0 0 24 24" width="24" height="24" '
         'fill="none" stroke="currentColor" stroke-width="1.25" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<path class="ar-shaft" d="M3.5 12h13"/>'
         '<path class="ar-head" d="m11.5 6.8 5.2 5.2-5.2 5.2"/></svg>')

# What a card holds, one 24-unit family drawn at 15px: a page for a document,
# a screen on its stand for a deck.
_PAGE = ('<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7" aria-hidden="true">'
         '<path d="M6 2.5h9l3 3V21a.5.5 0 0 1-.5.5h-11A.5.5 0 0 1 6 21z"/>'
         '<path d="M15 2.5V6h3M9 12h6M9 15.5h6"/></svg>')
_SLIDES = ('<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7" stroke-linecap="round" '
           'stroke-linejoin="round" aria-hidden="true"><path d="M2.5 4h19M4 4v11a1 1 0 0 0 1 1h14'
           'a1 1 0 0 0 1-1V4M12 16v3M8.5 21.5 12 19l3.5 2.5"/><path d="m8 12 2.5-2.5 2 2L16 8"/></svg>')

# The underbrace: an end, a run that stretches, the point, a run, an end; the
# runs are drawn in a box they stretch with, their stroke kept whole.
_RUN = ('<svg class="bpr__run bpr__run--{side}" viewBox="0 0 10 20" preserveAspectRatio="none">'
        '<path d="M0 10H10" vector-effect="non-scaling-stroke"/></svg>')
BRACE = ('<div class="bpr__brace" aria-hidden="true">'
         '<svg class="bpr__end" viewBox="0 0 12 20"><path d="M1 1C1 6.5 4.5 10 12 10"/></svg>'
         + _RUN.format(side="l") +
         '<svg class="bpr__tip" viewBox="0 0 28 20"><path d="M0 10C8.5 10 14 12 14 19'
         'C14 12 19.5 10 28 10"/></svg>'
         + _RUN.format(side="r") +
         '<svg class="bpr__end" viewBox="0 0 12 20"><path d="M0 10C7.5 10 11 6.5 11 1"/></svg></div>')


def _esc(text):
    return html.escape(text, quote=False)


def _attr(text):
    return html.escape(text, quote=True)


def _label(text):
    """A name, a slash kept with the word before it."""
    return _esc(text).replace(" / ", "&nbsp;/ ")


def _title(text):
    """A document's title kept whole where a break would hurt it, as rboxes.py
    and the document pages do: a slash or a bracketed abbreviation stays with
    the word before it ("Testing (NDT)" never leaves "(NDT)" alone on a line),
    and Non-destructive never breaks at its hyphen."""
    return (_label(text).replace(" (", "&nbsp;(")
            .replace("Non-destructive", '<span class="bpc__nb">Non-destructive</span>'))


def _count(n, thing):
    return f"{n} {thing}" if n == 1 else f"{n} {thing}s"


def families(categories=None):
    """The topics as the page groups them: [[category, ...], ...]. A topic
    that shares a document with the one before it joins its group, so a
    document shows once for all the topics it covers; a topic in preparation
    has its own page and stands alone."""
    out = []
    for c in categories or CATEGORIES:
        if out and set(c["docs"]) & set(out[-1][-1]["docs"]):
            out[-1].append(c)
        else:
            out.append([c])
    return out


def _icon(cid):
    """The home page's icon for a topic, the one that draws itself."""
    try:
        from parts.topics import _LIVE as icons
    except ImportError:
        try:
            from parts.topics import ICONS as icons
        except ImportError:
            return ""
    key = _ICON_OF.get(cid)
    return f'<span class="bpm__ic" aria-hidden="true">{icons[key]}</span>' if key in icons else ""


def _art(key, art):
    """A card's picture, or nothing where the build has none for it."""
    if not art or key not in art:
        return ""
    src, w, h = art[key]
    return (f'<span class="bpc__art"><img src="{_attr("art/" + src)}" width="{w}" '
            f'height="{h}" alt="" loading="lazy" decoding="async"></span>')


def _card(href, title, meta, art_html):
    """One card: its picture, his title, what it holds. The title's words
    are an inline of their own (.bpc__u), whose underline can run on from
    line to line."""
    return (f'<li><a class="bpc" href="{_attr(href)}">{art_html}'
            f'<span class="bpc__t"><span class="bpc__u">{_title(title)}</span></span>'
            f'<span class="bpc__m">{meta}{ARROW}</span></a></li>')


def _doc(slug, docs, art):
    held = f"{_PAGE}{_PAGES[slug]}-page read" if slug in _PAGES else "Word document"
    return _card(f"doc/{slug}.html", docs[slug][0], held, _art(slug, art))


def _deck(href, decks, art):
    return _card(href, decks[href][0], f"{_SLIDES}{_count(decks[href][2], 'slide')}",
                 _art(href, art))


def _node(c, k, docs, decks, art):
    """One topic, a column of the table: its node's number, its rail, icon,
    name, his line, and its cards (or its page in preparation)."""
    cid, soon = c["id"], bool(c.get("soon"))
    if soon:
        cards = [f'<li><a class="bpc bpc--soon" href="{_attr(c["soon"])}"><span class="bpc__art '
                 f'bpc__art--soon"><span class="bpc__t"><span class="bpc__u">In preparation</span></span>'
                 f'</span></a></li>']
    else:
        cards = [_doc(s, docs, art) for s in c["docs"] if s in docs]
        cards += [_deck(h, decks, art) for h in c.get("decks") or () if h in decks]
    line = f'<p class="bpm__line">{_esc(c["line"])}</p>' if c.get("line") else ""
    name = c.get("short") or c["label"]
    area = _AREA.get(cid, cid[:2])
    return (f'<section class="bpm__n bpm__n--{area}{" bpm__n--soon" if soon else ""}" id="{cid}" '
            f'aria-labelledby="bpm-{cid}"><span class="bpm__o" aria-hidden="true">{k}</span>'
            f'<span class="bpm__rail" aria-hidden="true"></span>'
            f'<div class="bpm__top">{_icon(cid)}<h2 class="bpm__h" id="bpm-{cid}">{_label(name)}</h2>'
            f'</div>{line}<ul class="bpm__docs" role="list">{"".join(cards)}</ul></section>')


def _research(docs, decks, art):
    """His research under the five: the brace, his sentence, his research
    documents and deck, and the way to My Research Areas."""
    cards = [_doc(s, docs, art) for s in RESEARCH if s in docs]
    cards += [_deck(h, decks, art) for h in RESEARCH_DECKS if h in decks]
    listed = f'<ul class="bpr__docs" role="list">{"".join(cards)}</ul>' if cards else ""
    return (f'<section class="bpr" aria-labelledby="bpr-h">{BRACE}'
            f'<h2 class="bpr__h" id="bpr-h">{_esc(RESEARCH_LINE)}</h2>{listed}'
            f'<p class="bpr__more"><a class="bpr__a" href="{_MORE[0]}">{_MORE[1]}{ARROW}</a></p>'
            f'</section>')


def _map(docs, decks, art):
    """The figure: the five topics with their cards, the layers the script
    draws the lines and their words into, his research under them, what a
    screen reader is told of the bridges, and the caption."""
    nodes = [_node(c, k, docs, decks, art) for k, c in enumerate(CATEGORIES, 1)]
    name = {c["id"]: c.get("short") or c["label"] for c in CATEGORIES}
    order = [c["id"] for c in CATEGORIES]
    shared = "".join(
        f"<li>{_esc(word)}, shared by "
        f"{' and '.join(_esc(name[x]) for x in sorted((a, b), key=order.index))}.</li>"
        for word, a, b in _BRIDGES if a in name and b in name)
    bridges = _attr(json.dumps([list(b) for b in _BRIDGES], separators=(",", ":")))
    return (f'<figure class="bpm" data-bridges="{bridges}" aria-labelledby="bpm-cap">'
            f'<div class="bpm__stage"><svg class="bpm__edges" aria-hidden="true" focusable="false"></svg>'
            f'<div class="bpm__words" aria-hidden="true"></div>{"".join(nodes)}</div>'
            f'{_research(docs, decks, art)}'
            f'<ul class="bp__vh">{shared}</ul>'
            f'<figcaption class="bpm__cap" id="bpm-cap">Each arc names an idea two topics share. '
            f'Every card opens its document or deck.</figcaption></figure>')


def render_big_picture(docs=None, decks=None, art=None):
    """Return the Big Picture page's body.

    `docs` is build.DOCS (slug -> (title, note, ...)); `decks` maps a deck's
    page to (title, note, slide count), the decks this build wrote, DECKS when
    None; `art` maps a document's slug or a deck's page to its picture under
    art/ as (file, width, height) (content/bigpicture/art.json)."""
    docs = {s: (v[0], v[1]) for s, v in docs.items()} if docs else _DOCS
    decks = DECKS if decks is None else decks
    return f"""<div class="wrap bp">
 <h1>Big Picture of Waves and Data Analytics</h1>
 <p class="lede bp__lede">Every document and slide deck on this site, by topic.</p>
 {_map(docs, decks, art)}
</div>"""
