# -*- coding: utf-8 -*-
"""Build the wavesanddata site for the Wix static-site drop.

    python build.py [--out DIR] [--strict]

Layout comes from the professor's own deck (content/source/NEW WAVES AND
DATA.pptx, four slides since 24 September 2026: the home page with its band
across the top and a twelve-row column, About Me, My Research Areas, the band
alone), measured out of the OOXML on his About and Research slides:

  sidebar   x 0 -> 2.23in of 13.33in   = 16.7% of the width, full height
  nav block solid accent1/lumMod75%    = #104862, white bold centred text
  active    accent2/lumMod50%          = #80350E
  cards     bg1/lumMod95% + bg2/lum90% = #F2F2F2 on #D1D1D1, rounded
  page      bg1                        = white

Those hexes are Office's default theme, darkened, so the palette was rebuilt
(design/DESIGN_BRIEF.md). His structure stays: a deep blue column on the
leading side, the identity above the nav block, a warm mark on the current
page. Every token lives in parts/theme.py; this file sets none.

Apple HIG informs the rest: sidebar on the leading side for top-level
navigation, one level, hidden only on narrow widths and never by default,
separators to group, most important content top-and-leading, and motion kept
short and reducible.
"""
import hashlib
import importlib
import html
import inspect
import json
import urllib.parse
import os
import re
import shutil
import sys
from urllib.parse import unquote, urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preview import render  # noqa: E402

SP = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SP)
OUT = os.path.join(SP, "dist")
BUILD = os.path.join(ROOT, "build", "ricos")
SRC = os.path.join(ROOT, "content", "source")
ICONS = os.path.join(SRC, "ppt-icons")

# Wix's limits. "Up to 3MB per file, up to 20MB in total" holds for a site
# uploaded through the dashboard (dev.wix.com/docs/go-headless/wix-managed-headless/
# other-frameworks/your-own-frontend/what-you-can-upload). This site is released
# from the terminal (build/release/site, `wix release`), where Wix takes "any
# build output" (.../wix-managed-headless/about-supported-frameworks): its two
# slide decks alone are some 28 MB. The file limit stays as a guard against one
# heavy file; the total is a ceiling for a mistake, not Wix's number.
WIX_FILE_MAX = 3_000_000     # bytes per file
WIX_SITE_MAX = 100_000_000   # bytes per site

# The seven documents, by the file name of each page under doc/.
SHORT = "brochure-shm-and-ndt-2-pages"
EXTENDED = "understanding-shm-and-ndt"
SOUND = "sound-detection-and-tracking"
WAVES = "dynamical-behavior-of-engineering-structures-and-acoustic-wave-propagation"
SIGNAL = "signal-processing-system-identification-and-optimization"
ML = "machine-learning-the-complete-picture-and-guide-5"
PHOTONS = "from-bridges-to-photons"

# --- the column, top to bottom (design/ROUND4_SPEC.md section 2): (href,
# title, sub-line, group). The titles and sub-lines are his, from the column
# he drew on slide 1 of his deck, and nav_report() holds them to it. Two
# changes are ours: a title drops the comma his slide uses to run it on into
# its sub-line, and his "Meetings, presentations. Reports. papers" takes commas
# throughout, its words unchanged. "Big Picture of Waves and Data Analytics"
# is the client's name for the page that maps every topic (NAV_OURS). Rows 5
# to 10 are his six topics: 5 to 7 open his three guides themselves, 8 to 10
# pages in preparation. Since 25 Sep 2026 the column does not show them as
# rows: the Big Picture row's list names them (parts/bpnav.py), and he asked
# that they not stand in the column a second time. They stay here because the
# home page's topic cards are these rows, the pages in preparation take their
# titles and sub-lines from them, and nav_report() still holds his words to
# his slide; nav_html() leaves them out. "group" opens a group, one hairline
# above its first row: {About Me, My Research Areas, Gallery}, {the Big
# Picture and its list}, {Blog, Contact}. The no-break space keeps "System
# Identification" whole where the title wraps, on its topic card.
BIG_PICTURE = "Big Picture of Waves and Data Analytics"
NAV = [
    ("about.html", "About Me", "", ""),
    ("research.html", "My Research Areas", "Sound Waves, NDT, SHM", ""),
    ("gallery.html", "Gallery", "", ""),
    ("big-picture.html", BIG_PICTURE, "", "group"),
    (f"doc/{WAVES}.html", "Vibrations and Waves", "All vibrations are waves", ""),
    (f"doc/{SIGNAL}.html", "Signal Processing, System\u00a0Identification",
     "Estimation, Inverse Problems, Optimization, Machine Learning", ""),
    (f"doc/{ML}.html", "Machine Learning",
     "Neural and non-neural methods, Data Science vs ML Engineer", ""),
    ("probability-statistics.html", "Probability, Statistics",
     "Stochastic Process, Estimation", ""),
    ("python-programming.html", "Python / Programming", "", ""),
    ("blog.html", "Blog", "", "group"),
    ("communication.html", "Communication", "Meetings, presentations, reports, papers", ""),
    ("personal-advices.html", "Personal Advices on Working on a Project", "", ""),
    ("contact.html", "Contact", "", ""),
]
# rows whose words are not on his slide: the Big Picture, our name for his
# map, and the section his notes of 5 Oct 2026 asked for ("Make a section
# called 'Personal Advices on Working on a Project' and say under construction")
NAV_OURS = frozenset(("big-picture.html", "personal-advices.html"))
# Of his topics, the one that keeps a row of its own in the column, after Blog:
# the professor took Communication out of the Big Picture on 26 Sep 2026
# ("Communication da orada olmayacak, solda menüde olacak"). The others are
# named in the Big Picture row's list (nav_html()).
OWN_ROW = frozenset(("communication.html",))

# Rows 5 to 10 are also the home page's six topic cards (parts/topics.py):
# each card's text is its row's sub-line, and `icon` names the subject the
# card draws. A card whose page is still in preparation says so (soon).
TOPIC_ICONS = {
    f"doc/{WAVES}.html": "vibrations-waves",
    f"doc/{SIGNAL}.html": "signal-processing",
    f"doc/{ML}.html": "machine-learning",
    "probability-statistics.html": "probability-statistics",
    "python-programming.html": "python-programming",
    "communication.html": "communication",
}

# Each document by the <h1> of its page, which page_doc() takes from the cover
# of his own document: his title, his capitals, his "Behavior". The Big
# Picture page, the research boxes and the pages in preparation name them the
# same way, so a link and the page it opens agree; page_doc() warns when a
# title here drifts from the cover. The note under a title is ours.
DOCS = {
    SHORT: (
        "Structural Health Monitoring (SHM) and Non-destructive Testing (NDT)",
        "A two-page introduction to both fields.", "image4.png"),
    EXTENDED: (
        "Understanding Structural Health Monitoring and Nondestructive Testing: "
        "A Casual Introduction",
        "The same ground, at length.", "image6.png"),
    SOUND: (
        "Understanding Sound Classification, Localization and Tracking and "
        "Similarity to NDT",
        "Acoustic wave-based monitoring.", "image5.png"),
    WAVES: (
        "Dynamical Behavior of Engineering Structures and Acoustic Wave Propagation",
        "The vibrations and waves guide.", ""),
    SIGNAL: (
        "Signal Processing, System Identification, Estimation Theory and "
        "Optimization with the underlying logic of machine learning",
        "The data side of the work.", ""),
    ML: (
        "Machine Learning",
        "Twelve sections, from what machine learning is to how to learn it.", ""),
    PHOTONS: (
        "From Bridges to Photons: Mode Shapes and Wave Propagation in Quantum "
        "Mechanics",
        "A short piece.", ""),
}

SRC_DOCX = {
    SHORT: "Brochure - SHM and NDT - 2 pages.docx",
    EXTENDED: "Understanding_SHM_and_NDT.docx",
    SOUND: "Sound Detection and Tracking.docx",
    WAVES: "Dynamical_Behavior_of_Engineering_Structures_and_Acoustic_Wave_Propagation.docx",
    SIGNAL: "Signal Processing, System Identification, and Optimization.docx",
    ML: "Machine Learning - The Complete Picture and Guide_5.docx",
    PHOTONS: "From_Bridges_to_Photons.docx",
}

# The Word originals that ship, byte for byte, beside their pages as
# doc/<slug>.docx: a name with no spaces, which every link uses, while each
# link's download attribute gives the saved copy his own file name. Each was
# audited first: no email address, no Word comments, no tracked changes,
# under 3 MB. The other four stay offline: Signal Processing carries his
# personal Gmail, From Bridges to Photons carries Word comments, and the
# Dynamical Behavior (3.97 MB) and Machine Learning (10.29 MB) guides are over
# Wix's per-file limit. Their links sit under the research boxes and on these
# three document pages, and nowhere else.
HOSTED_DOCX = (SHORT, EXTENDED, SOUND)

# Short labels for the seven documents, ours. The column no longer lists the
# documents; tools/wix_import.py still labels each one with these in the Wix
# Studio copy.
DOC_LABELS = {
    SHORT: "SHM and NDT (Short)",
    EXTENDED: "SHM and NDT (Extended)",
    SOUND: "Sound Wave Tracking",
    WAVES: "Dynamical Behavior and Waves",
    SIGNAL: "Signal Processing and Optimization",
    ML: "Machine Learning",
    PHOTONS: "From Bridges to Photons",
}

# Where each document lives, for the column's mark and the crumb above its
# title. The three SHM/NDT documents are the ones My Research Areas
# introduces; the other four sit in the Big Picture: each marks that row, and
# its crumb leads there. Round 4 made his three guides rows of their own (5 to
# 7), each marking its own row with no crumb, since a crumb up to the Big
# Picture would have filed them under it, which the client ruled out then
# (ROUND4_SPEC.md section 2). On 25 Sep 2026 the professor took his topics out
# of the column: clicking Big Picture opens its list, so they need not be
# rows as well. The guides are now filed under the Big Picture like every
# topic: on its page a guide is marked in the list (nav_html()), the Big
# Picture row is its section, and its crumb leads up to it. From Bridges to
# Photons is marked there under Waves and Dynamics.
DOC_HOME = {SHORT: "research.html", EXTENDED: "research.html", SOUND: "research.html",
            WAVES: "big-picture.html", SIGNAL: "big-picture.html", ML: "big-picture.html",
            PHOTONS: "big-picture.html"}

# A top-level page without a row of its own marks the row it belongs to: the
# CV is About Me's.
PAGE_SECTION = {"cv.html": "about.html"}

# The pages in preparation (parts/soon.py), rows 9 and 10: each shows his
# label and sub-line and links the pages already written that the topic draws
# on. Every link is named by the page it opens: a guide by its own title. Row 8,
# Probability, Statistics, is his deck of that name (parts/deck.py, in main()).
SOON = {
    "python-programming.html": (f"doc/{ML}.html", f"doc/{SIGNAL}.html"),
    "communication.html": ("blog.html", "research.html"),
    "personal-advices.html": ("communication.html", "blog.html"),
}
# A page in preparation says so in his words where he chose them: "under
# construction" for his advice section (5 Oct 2026); the others are in
# preparation (parts/soon.py draws the state).
SOON_STATE = {"personal-advices.html": "Under construction"}

# The CV (parts/cv.py): content/cv/cv.json, which tools/cv_extract.py writes
# from his Word CV. The Word file itself never ships (private_report()): it
# carries a personal Gmail and phone number, and so must nothing else here.
CV_JSON = os.path.join(ROOT, "content", "cv", "cv.json")
CV_DOCX = os.path.join(SRC, "Korkut_Kaynardag_Resume.docx")
LINK_KINDS = ("scholar", "linkedin", "researchgate", "github", "youtube")
# About and Contact show only these three, as slide 2 does; GitHub and YouTube
# are part of his CV's header and appear on cv.html alone (ROUND4_SPEC.md
# section 12).
PROFILE_KINDS = ("scholar", "linkedin", "researchgate")


# ---------------------------------------------------------------------------
# The professor's own words, transcribed from NEW WAVES AND DATA.pptx and
# shipped as he wrote them, grammar and punctuation included: "his M.Sc.",
# "his Ph.D." and "After completing his doctorate, he continued his career"
# inside sentences that begin "I", "followings", "In mechanic and physic
# side", the straight apostrophes he typed, and, from his editorial markup of
# 27 Sep 2026, "teach your mathematics" and "rather than make you". None of
# it is ours to correct; a change needs his written OK (APPROVED_EDITS).
# The markup is ours: the tags, the link on "about me", and the nowrap spans
# that keep a year range on one line. A --strict build checks every paragraph,
# list item and heading of each block against the text of its slide
# (deck_report()).
# ---------------------------------------------------------------------------

# slides 1 and 4: the band across the top of the home page. His deck types the
# power with Unicode superscript digits, "10²⁷"; here it is MathML, so a screen
# reader reads a power of ten where a <sup> was read out as "10 27" (round-4
# finding A11Y-4), and deck_report() reads the <msup> back as those digits.
# The markup is ours; a <math> is one box that never breaks across a line, so
# "7 × 10²⁷" stays whole. It is inline HTML with no block around it:
# parts/masthead.py sets it in its own element and sizes the power.
PROF_HEADER = """From elastic waves causing dynamic vibrations in a bridge to the matter waves
inside a single atom (fun fact: roughly <math><mn>7</mn> <mo>&times;</mo> <msup><mn>10</mn><mn>27</mn></msup></math> atoms in a
human body), wave motion sits at the center of the physical world. What we observe, though,
arrives as discrete measurements. Data analytics is how we recover the information behind
those numbers, and how we make it useful."""

# slide 1, as he revised it with us (meeting notes, Sep 2026): four items,
# the third the Big Picture and its topics. Not held to the slide any more.
# His words are unchanged; each topic links to its own group on the Big
# Picture page, as the map's pills do, where the rail and the wash mark the
# arrival (big-picture.html is no document, so a place in it may be linked).
PROF_INTRO = """<p class="lede">This webpage introduces you to followings:</p>
<ol class="introlist">
 <li><a class="inlink" href="about.html">Myself</a></li>
 <li><a class="inlink" href="research.html">My Research</a></li>
 <li><a class="inlink" href="big-picture.html">Big Picture of Waves and Data Analytics</a>:
  <ul><li><a class="inlink" href="big-picture.html#waves-dynamics">Waves, Dynamics</a></li>
      <li><a class="inlink" href="big-picture.html#signal-processing">Signal Processing, System Identification, Estimation Theory, Optimization</a></li>
      <li><a class="inlink" href="big-picture.html#machine-learning">Machine Learning</a></li>
      <li><a class="inlink" href="big-picture.html#python-programming">Python / Programming</a></li></ul></li>
 <li><a class="inlink" href="blog.html">Blog</a> / <a class="inlink" href="communication.html">Communication tips</a></li>
</ol>"""

# slide 1
PROF_BIO = """<p><strong>Myself:</strong></p>
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

# slide 1, as his editorial markup of 27 Sep 2026 changed it (APPROVED_EDITS):
# the topics he added to the first paragraph, his typed note as the first
# point, the old first point after the second, and the sentences he typed
# into the last paragraph, which he asked to be bold
PROF_MOTIVATION = """
 <h2>Motivation for Creating the Educational Sections</h2>
 <div class="col">
  <p>As a civil engineer, I only encountered topics like vibrations, waves, signals, system
  identification, probability, statistics, estimation, stochastic process, machine learning,
  Python and programming after completing my undergraduate studies. This made learning them
  particularly challenging. It took me a long time, with repeated study, to truly grasp:</p>
  <ul>
   <li>What methods are in each topic, what they actually do (the intuition and logic), and
   thus what the big picture of each topic is</li>
   <li>What kinds of problems they solve and where these methods are applied</li>
   <li>How similar concepts reappear across different fields</li>
   <li>How deeply interconnected they actually are</li>
  </ul>
  <p>That final realization was my &ldquo;Aha!&rdquo; moment.</p>
  <p>My goal in creating these educational sections is to shorten your learning journey.
  <strong>These sections are designed not to teach your mathematics of each method/algorithm,
  but rather than make you figure out the answers of the 4 questions above.
  Accordingly,</strong> I aim to help you understand these topics more quickly and clearly, so
  you can spend less time struggling with the basics and more time applying them meaningfully
  in your work.</p>
 </div>
"""

# slide 2, with the eight runs he set in bold there
PROF_ABOUT = """<p>I received his bachelor's and <strong>master's degrees</strong> from the
Department of Civil Engineering at <strong>Bo&#287;azi&ccedil;i University in 2013 and
2016</strong>, respectively, and his <strong>Ph.D.</strong> from the Department of Civil
Engineering at <strong>The University of Texas at Austin in 2023</strong>.</p>
<p>I served as a project assistant at Bo&#287;azi&ccedil;i University from 2013 to 2014 and
as a research assistant from 2014 to 2016, followed by a graduate research assistantship at
The University of Texas at Austin from 2016 to 2023. After completing his doctorate, he
continued his career in the United States, working as an <strong>Applied Data Scientist at
Transtek International Group</strong> from 2023 to 2024 and as a <strong>Senior AI Engineer at
Renesas Electronics America</strong> from 2024 to 2026.</p>
<p>Since August 27, 2026, I have served as an <strong>Assistant Professor</strong> in the
Department of Civil Engineering at <strong>Izmir Institute of Technology</strong>, where my
research focuses on structural health monitoring, nondestructive damage detection, smart
sensors, and smart cities.</p>
<p>As of September 2026, I have 12 published articles; 2 patents, one granted and the other
pending; and 8 awards received through academic and industry-academia collaborative research
grants.</p>"""

# slide 3, beside the four boxes, as his editorial markup of 27 Sep 2026
# changed it (APPROVED_EDITS); his second paragraph moved to the section below
PROF_RESEARCH = """<p class="lede">My research focuses on Structural Health Monitoring (SHM) and
  Non-Destructive Testing (NDT): the science of monitoring and testing structures to detect and
  characterize defects before they become failures. Because these fields rely heavily on
  vibration analysis, acoustic wave propagation, data analytics, and machine learning, my path
  also took me to industry, where I worked as an applied data scientist and a Senior AI Engineer
  on sound source tracking. The three documents on the right introduce my research topics, and
  I've also included a presentation that walks through my master's and PhD work in more
  depth.</p>"""

# slide 3, the section under his text, as his editorial markup of 27 Sep 2026
# left it (APPROVED_EDITS, STRUCK): its heading, ours, with the words he added
# to it; his second paragraph, which he moved here; the section's own two
# paragraphs he struck
PROF_RESEARCH_MORE = """<h2>The educational sections (topics in the big picture menu)</h2>
  <p>You'll also find documents about the topics that I used extensively in the <a class="inlink" href="big-picture.html">Big Picture</a> menu on
  the left. I wrote them for newcomers who want the big picture: how these topics connect, and
  how to approach learning them, without diving into the equations and formalism of a textbook
  or lecture. They reflect my own path into this field, but everyone's path is different, so
  I'd encourage you to read a few other guides alongside these rather than relying on just
  one.</p>"""

# Where he is, as his CV gives it ("Izmir, Turkiye"), with the one address the
# site carries: his institutional email.
CONTACT = {
    "department": "Department of Civil Engineering",
    "institution": "Izmir Institute of Technology",
    "city": "Izmir, Turkiye",
    "email": "korkutkaynardag@iyte.edu.tr",
    # his personal address, public for contact since 29 Sep 2026 at the client's
    # word ("korkut.kaynardag@gmail.com iletisim icin sitede olsun hep")
    "personal": "korkut.kaynardag@gmail.com",
}
# the two addresses the site may carry; any other stops the build
PUBLIC_EMAILS = frozenset((CONTACT["email"], CONTACT["personal"]))


CSS = """
/* The base stylesheet: the shell, and the furniture build.py writes itself.
   Every token (colour, type stack, radius, motion) is defined once, in
   parts/theme.py, which parts.css carries after this file. None is set here. */
*{box-sizing:border-box}
/* No smooth scrolling: a jump from a contents list or an anchor lands at
   once. Smoothed, it scrolled up to 70,000px of text past the reader over
   1.5s, a full-screen movement the motion rules do not allow. */
html{-webkit-text-size-adjust:100%;scrollbar-gutter:stable}
body{margin:0;background:var(--page);color:var(--body)}
img{max-width:100%}
::selection{background:var(--wash);color:var(--ink)}
/* the body link: underline at rest, the line firms up on hover */
a{color:var(--link);text-decoration-line:underline;text-decoration-thickness:1.5px;
  text-underline-offset:3px;
  text-decoration-color:color-mix(in oklab,currentColor,transparent 62%);
  transition:text-decoration-color var(--t-fast) var(--ease-state)}

.skip{position:fixed;left:16px;top:16px;z-index:60;padding:13px 18px;
  border-radius:var(--r-sm);background:var(--page);color:var(--ink);box-shadow:var(--sh-2);
  font:600 15px/1.2 var(--sans);text-decoration:none}
.skip:not(:focus){clip-path:inset(50%);width:1px;height:1px;padding:0;overflow:hidden;
  white-space:nowrap}

/* ---------- the column: identity above the nav block, full height ---------- */
.side{position:fixed;inset:0 auto 0 0;width:var(--side);z-index:40;background:var(--page);
  display:flex;flex-direction:column;overflow-y:auto;overscroll-behavior:contain}
.id{display:block;color:inherit;text-decoration:none}
.id b,.id span{display:block}
.nav{list-style:none;margin:0;padding:0;background:var(--nav);flex:1 0 auto}
.nav a{text-decoration:none}
/* overlap the nav block by 1px: two navy boxes meeting on a fractional pixel
   let a paper-coloured seam through */
.side__end{background:var(--nav);flex:1 1 auto;min-height:0;margin-top:-1px}
.bar,#scrim{display:none}

/* ---------- content ---------- */
.main{margin-left:var(--side);min-height:100vh;background:var(--page)}
.wrap{max-width:1020px;margin:0 auto;padding:56px 48px 0}
.col{max-width:var(--measure)}
/* the 44px Download line under the research boxes already leaves 12px of air
   below its text; the heading after them takes the rest of its 47px */
.rboxes+h2{margin-top:35px}
/* his research text opens with a paragraph marked as a lede; it runs to ten
   lines, so it reads at the size of the paragraph that follows it */
.col--his .lede{font-size:inherit;line-height:inherit;letter-spacing:0}
p{margin:0 0 1.15em}
ul,ol{margin:0 0 1.2em;padding-left:1.35em}
li{margin:.35em 0}
hr{border:0;border-top:1px solid var(--rule);margin:56px 0 0}
.soon{color:var(--muted)}
.nw{white-space:nowrap}

/* his intro list */
.introlist{margin:0 0 1.3em;padding-left:1.4em}
.introlist>li{margin:.42em 0}
.introlist ul{margin:.45em 0 .2em;padding-left:1.1em;list-style:none}
.introlist ul li{position:relative;color:var(--muted);margin:.3em 0}
.introlist ul li::before{content:"";position:absolute;left:-14px;top:.8em;width:7px;
  height:1px;background:var(--line)}

/* ---------- in preparation ---------- */
.pending{border-left:1px solid var(--line);padding:2px 0 2px 20px;margin:4px 0 0}
.pending__tag{display:block;margin:0 0 10px;font:600 12px/1.1 var(--sans);
  letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.pending p{margin:0;color:var(--muted)}

/* ---------- a list of documents, one row each ----------
   The Gallery's row (parts/gallery.py): lit, the fill is one rounded shape
   bled 12px past the words, and the hairlines that touch it fade out, so it
   never reads as a band pinned between two rules. A press takes the fill
   one step deeper, 5% to 8% ink, as every row and card on the site does. */
.rows{position:relative;margin:24px -12px 0}
.rows::before,.row::after{content:"";position:absolute;left:12px;right:12px;
  border-top:1px solid var(--rule);transition:opacity var(--t-quick) var(--ease-state)}
.rows::before{top:0}
.row{position:relative;display:flex;gap:24px;align-items:center;
  justify-content:space-between;padding:16px 12px;border-radius:var(--r-sm);
  color:inherit;text-decoration:none;-webkit-tap-highlight-color:transparent;
  transition:background-color var(--t-quick) var(--ease-state)}
.row::after{bottom:0}
.row b{display:block;font:600 19px/1.35 var(--serif);color:var(--ink);text-wrap:pretty}
.row em{display:block;margin-top:4px;font:400 16px/1.5 var(--serif);color:var(--muted);
  text-wrap:pretty}
.row__go{flex:none;display:inline-flex;align-items:center;color:var(--muted);
  transition:color var(--t-quick) var(--ease-state)}
.row__go svg{flex:none}
/* the arrow, as rboxes.py and gallery.py move it. At rest the shaft stops at
   the open end of the head, so it reads as one arrow (the brief's offset of 9
   left a gap that read as a typed "->"). On hover the shaft draws over 240ms
   and the head slides 5px, 60ms behind it; letting go is quicker and
   unstaggered. A key that lands on a row finds the arrow already drawn:
   keyboard focus takes the end state at once, the travel is the pointer's
   (round-4 finding RM-7). Asked for less motion, the arrow stands finished. */
@media (prefers-reduced-motion:no-preference){
  .row .ar-shaft{stroke-dasharray:13;stroke-dashoffset:5;
    transition:stroke-dashoffset var(--spring-fast)}
  .row .ar-head{transition:transform var(--spring-fast)}
}
@media (hover:hover) and (prefers-reduced-motion:no-preference){
  .row:hover .ar-shaft{stroke-dashoffset:0;transition-duration:var(--t-mid)}
  .row:hover .ar-head{transform:translateX(5px);
    transition:transform var(--spring-mid) 60ms}
}
@media (prefers-reduced-motion:no-preference){
  .row:focus-visible .ar-shaft{stroke-dashoffset:0;transition:none}
  .row:focus-visible .ar-head{transform:translateX(5px);transition:none}
}

/* ---------- about: his text beside the portrait ---------- */
.hero{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:48px;align-items:start}
.hero img{display:block;width:100%;height:auto;border-radius:var(--r-md)}
.about{margin-top:32px}
.about>div>:last-child{margin-bottom:0}    /* else trapped in the grid cell */
.about>div:first-child{max-width:var(--measure)}
@media (max-width:1100px){
  .hero{grid-template-columns:minmax(0,1fr)}
  .hero img{max-width:220px}
}
.about__aside p{margin:20px 0 0;font-size:16px;line-height:1.5}
.links{display:flex;flex-wrap:wrap;gap:8px 28px;list-style:none;padding:0;margin:16px 0 0;
  font-size:16px;line-height:1.5;color:var(--muted)}
.links li{margin:0}
.links--stack{flex-direction:column;gap:6px}

/* ---------- contact ---------- */
.find{list-style:none;padding:0;margin:24px 0 0}
.find li{margin:0 0 24px}
.find b{display:block;font-weight:600;color:var(--ink)}
.find em{display:block}
.find a{position:relative;overflow-wrap:anywhere}
.find a::after{content:"";position:absolute;inset:-9px -4px}

/* ---------- a Word file not up yet: its download line waits ----------
   (a document page, a post, under --no-word) in the research boxes' words */
.docpage .docdl.docdl--wait{color:var(--muted);cursor:default}
.docpage .docdl--wait svg{opacity:.75}

/* ---------- used only while a part module is missing ---------- */
.mastfb{background:var(--nav-deep);color:var(--nav-ink);padding:20px 48px}
.mastfb p{max-width:1100px;margin:0 auto;font:400 17px/1.6 var(--serif);text-align:center}
@media (max-width:1000px){.mastfb{padding:16px 22px}.mastfb p{font-size:16px;text-align:left}}
.boxes{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:24px 20px;
  margin:24px 0 0}
.boxes>div{display:flex;flex-direction:column}
.box{flex:1 1 auto;display:flex;flex-direction:column;gap:8px;padding:24px 0 20px;
  border-top:1px solid var(--rule);color:var(--ink);text-decoration:none;
  transition:background-color var(--t-quick) var(--ease-state)}
.box b{font:600 19px/1.35 var(--serif)}
.box em{font:400 16px/1.5 var(--serif);color:var(--muted)}
.box img{width:56px;height:56px;margin-top:8px}
.dl{display:inline-flex;align-items:center;min-height:44px;font:600 15px/1.2 var(--sans);
  color:var(--link)}
.stats{display:flex;gap:56px;flex-wrap:wrap;margin:24px 0 0}
.stats b{display:block;font:600 40px/1 var(--serif);color:var(--accent)}
.stats span{display:block;font-size:16px;color:var(--muted);margin-top:8px}
.tl{list-style:none;padding:0;margin:24px 0 0}
.tl li{display:grid;grid-template-columns:132px minmax(0,1fr);gap:24px;margin:0;
  padding:18px 0;border-top:1px solid var(--rule)}
.tl time{color:var(--muted);padding-top:3px}
.tl h3{margin:0 0 4px;font-size:19px}
.tl p{margin:0;font-size:16px;color:var(--muted)}
.btn{display:inline-flex;align-items:center;min-height:44px;padding:0 22px;
  border:1px solid var(--line-strong);border-radius:var(--r-pill);color:var(--ink);
  text-decoration:none;font:600 15px/1.2 var(--sans);letter-spacing:.01em;
  transition:background-color var(--t-fast) var(--ease-state),
    border-color var(--t-fast) var(--ease-state)}
.btn:active{background:var(--rule)}

/* ---------- footer ---------- */
/* On a page shorter than the window the footer sits at its foot: sticky with
   top:100vh pushes it down only as far as .main's min-height allows, and on a
   long page it has nowhere to go. Its rule spans the text, not the padding. */
.foot{position:sticky;top:100vh;max-width:1020px;margin:96px auto 0;
  padding:32px 48px 48px;font:400 14px/1.6 var(--serif);color:var(--muted);
  display:flex;gap:24px 32px;justify-content:space-between;flex-wrap:wrap;
  align-items:flex-start;
  /* off screen it is skipped: the credit's wave drifts for ever, and laid out
     with the page it made every frame of any other motion lay out and paint
     the page again (MotionScore, 5 Oct 2026) */
  content-visibility:auto;contain-intrinsic-size:auto 160px}
.foot::before{content:"";position:absolute;top:0;left:48px;right:48px;
  border-top:1px solid var(--rule)}
.foot p{margin:0}
.foot b{color:var(--ink);font-weight:600}
.foot nav{display:flex;flex-wrap:wrap;gap:0 24px;margin-top:-11px}
/* a link is 44px tall and as wide as its word, so the gaps between the words
   are the row's 24px (a 44px minimum width left a wider gap after "Blog"), and
   a wrapped row of links starts where the one above it does */
.foot a{display:inline-flex;align-items:center;justify-content:flex-start;min-height:44px;
  color:var(--muted);
  text-decoration-color:transparent;
  transition:color var(--t-fast) var(--ease-state),
    text-decoration-color var(--t-fast) var(--ease-state)}

/* the credit: its own line at the foot's right (left on a phone), quiet
   until pointed at. The wave drifts a wavelength every 2.4s in the warm, two
   wavelengths a second under the pointer, and the name's letters rise 2px
   one after another, 40ms apart; asked for less motion, nothing moves. */
.foot__credit{flex:1 0 100%;margin:-8px 0 0!important;text-align:right}
.credit{display:inline-flex;align-items:center;flex-wrap:wrap;justify-content:flex-end;
  gap:2px 10px;font:400 12px/1.4 var(--sans);letter-spacing:.08em;color:var(--muted)}
.credit__wave{flex:none;overflow:hidden;color:var(--accent)}
.credit__wave path{fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round}
.credit__what{text-transform:uppercase;font-size:12px}
.credit__sep,.credit__said{position:absolute;width:1px;height:1px;overflow:hidden;
  clip-path:inset(50%);white-space:nowrap}
.credit__name{font:600 14px/1.4 var(--serif);letter-spacing:.01em;color:var(--ink)}
.credit__shown i{display:inline-block;font-style:normal}
@media (max-width:640px){.foot__credit{text-align:left}.credit{justify-content:flex-start}}
@media (prefers-reduced-motion:no-preference){
  .credit__wave path{animation:credit-drift 2.4s linear infinite}
  .credit__shown i{transition:transform var(--spring-fast),color var(--t-quick) var(--ease-state);
    transition-delay:calc(var(--i) * 40ms)}
}
@media (hover:hover) and (prefers-reduced-motion:no-preference){
  .credit:hover .credit__wave path{animation-duration:.5s}
  .credit:hover .credit__shown i{transform:translateY(-2px);color:var(--accent)}
}
@keyframes credit-drift{to{transform:translateX(18px)}}

/* ---------- states: hover only where a pointer can hover ---------- */
@media (hover:hover){
  a:hover{text-decoration-color:currentColor}
  .row:hover,.box:hover{background:color-mix(in oklab,var(--ink) 5%,var(--page))}
  .row:hover .row__go{color:var(--body)}
  .btn:hover{background:var(--card);border-color:var(--ink)}
  .burger:hover{background:color-mix(in oklab,var(--ink) 5%,var(--page))}
  .foot a:hover{color:var(--ink);text-decoration-color:currentColor}
}
/* one ring for every link; a part may place it differently */
a:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.box:focus-visible,.foot a:focus-visible{border-radius:var(--r-sm)}
.row:focus-visible{background:color-mix(in oklab,var(--ink) 5%,var(--page))}
.row:focus-visible .row__go{color:var(--body)}
.row:active{background:color-mix(in oklab,var(--ink) 8%,var(--page))}
/* Forced colours paint no fill, so there hover and press keep the hairlines;
   the focus ring takes their place. The :has() rules stand alone, so a
   browser without :has() drops only them. */
@media (hover:hover) and (forced-colors:none){.row:hover::after{opacity:0}}
@media (hover:hover) and (forced-colors:none){.rows:has(>.row:hover)::before{opacity:0}}
@media (forced-colors:none){.row:active::after{opacity:0}}
@media (forced-colors:none){.rows:has(>.row:active)::before{opacity:0}}
.row:focus-visible::after{opacity:0}
.rows:has(>.row:focus-visible)::before{opacity:0}

/* ---------- narrow: the column folds into a drawer (HIG) ---------- */
@media (max-width:1000px){
  /* focus and jumps land clear of the sticky bar: 60px, its rule, 15px of air */
  html{scroll-padding-top:76px}
  .main{margin-left:0;min-height:calc(100vh - 60px);min-height:calc(100svh - 60px)}
  .wrap,.foot{padding-inline:22px}
  .foot::before{left:22px;right:22px}
  .bar{display:flex;position:sticky;top:0;z-index:30;align-items:center;
    justify-content:space-between;gap:16px;min-height:60px;padding:8px 8px 8px 22px;
    background:var(--page);border-bottom:1px solid var(--rule)}
  /* his portrait, small, before his name: on a phone, his face on every
     page, the column's file and its hairline rim (parts/theme.py) */
  .bar .bar__id{display:inline-flex;align-items:center;gap:10px;min-height:44px;
    font:600 17px/1.2 var(--serif);letter-spacing:-.004em;color:var(--ink);
    text-decoration:none}
  .bar__pic{flex:none;display:block;width:32px;height:32px;border-radius:50%;
    background:var(--card);
    outline:1px solid color-mix(in oklab,var(--ink) 10%,transparent);outline-offset:-1px}
  /* the menu is a button that says whether the drawer is open (aria-expanded).
     The script runs it, so without one it is not drawn and the footer's
     links stand in for the drawer. */
  .burger{flex:none;display:none;place-content:center;gap:4px;width:44px;height:44px;
    margin:0;padding:0;border:0;border-radius:var(--r-sm);background:transparent;
    color:var(--ink);font:inherit;cursor:pointer;-webkit-tap-highlight-color:transparent;
    transition:background-color var(--t-quick) var(--ease-state)}
  .js .burger{display:grid}
  .burger i{display:block;width:20px;height:1.5px;background:currentColor}
  .burger:active{background:color-mix(in oklab,var(--ink) 8%,var(--page))}
  .burger:focus-visible{outline:2px solid var(--focus);outline-offset:-2px}
  /* closed, the drawer also leaves the tab order, once it has slid away */
  .side{transform:translateX(-102%);visibility:hidden;box-shadow:var(--sh-3);
    transition:transform var(--spring-mid),visibility 0s linear var(--t-mid)}
  .nav-open .side{transform:none;visibility:visible;
    transition:transform var(--spring-mid)}
  #scrim{display:block;position:fixed;inset:0;z-index:35;background:rgba(39,34,28,.34);
    opacity:0;pointer-events:none;transition:opacity var(--t-mid) var(--ease)}
  .nav-open #scrim{opacity:1;pointer-events:auto}
  .tl li{grid-template-columns:minmax(0,1fr);gap:4px}
}
@media (max-width:560px){
  .row{gap:16px}
  /* the footer's links wrap to two rows on a phone; 20px gaps keep each row
     even (with 24px and the first four, Contact fell to a line of its own) */
  .foot nav{column-gap:20px}
}
@media (forced-colors:active){.burger i{background:CanvasText}}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{transition:none!important}
}
"""

# The phone drawer's menu button, a real button (round-4 finding A11Y-6: a
# checkbox was announced "Menu, checkbox, not checked"). A click opens or
# closes the drawer and the scrim closes it; Escape closes the open drawer and
# hands focus back to the button; focus leaving the open drawer closes it, so
# a keyboard never lands on a link the drawer covers (WCAG 2.4.11); a window
# that grows past 1000px, where there is no drawer, closes it. The state is
# .nav-open on <html>, which the stylesheet reads, and aria-expanded on the
# button, which a screen reader reads.
#
# The column's scroll cue (parts/theme.py, THE COLUMN): .nav--more on the
# list while the box that scrolls it (the list itself on a desktop, the whole
# drawer on a phone) is not at its end, checked on scroll, on resize and when
# a row changes size (a list opened inside the column).
JS = """
var html=document.documentElement,btn=document.querySelector('.burger'),
  side=document.getElementById('site-nav'),scrim=document.getElementById('scrim');
if(!side)return;
var list=side.querySelector('.nav');
function more(){
  if(!list)return;
  var box=list.scrollHeight>list.clientHeight+1?list:side;
  list.classList.toggle('nav--more',box.scrollHeight-box.clientHeight-box.scrollTop>1);
}
if(btn){
  var set=function(open){
    html.classList.toggle('nav-open',open);
    btn.setAttribute('aria-expanded',open?'true':'false');
    if(open)more();
  };
  var shut=function(){set(false);};
  btn.addEventListener('click',function(){set(!html.classList.contains('nav-open'));});
  if(scrim)scrim.addEventListener('click',shut);
  addEventListener('keydown',function(e){
    if(e.key==='Escape'&&html.classList.contains('nav-open')){shut();btn.focus();}
  });
  side.addEventListener('focusout',function(e){
    var to=e.relatedTarget;
    if(html.classList.contains('nav-open')&&to&&to!==btn&&!side.contains(to))shut();
  });
  var wide=matchMedia('(width > 1000px)');
  if(wide.addEventListener)wide.addEventListener('change',function(e){if(e.matches)shut();});
}
if(list){
  list.addEventListener('scroll',more,{passive:true});
  side.addEventListener('scroll',more,{passive:true});
  addEventListener('resize',more);
  if(window.ResizeObserver){
    var ro=new ResizeObserver(more);
    ro.observe(list);
    for(var i=0;i<list.children.length;i++)ro.observe(list.children[i]);
  }
  more();
}
"""

ICON = {
    "download": '<path d="M12 5v10m-4.5-4.5L12 15l4.5-4.5M6 19h12"/>',
}


def svg(name):
    """An inline icon: 24-unit grid, drawn at 20px with a 1.5 stroke."""
    return ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
            'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" '
            f'aria-hidden="true">{ICON[name]}</svg>')


# The site's arrow, the markup parts/rboxes.py and parts/gallery.py draw: two
# paths, so the shaft can draw while the head travels. At 24px one unit is one
# pixel, so the head's 5-unit slide is the brief's 5px (at 18px it was 3.75px),
# and stroke 1.25 is the inline family's 1.25px line (DESIGN_BRIEF.md 4.1, 7.1).
ARROW = ('<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" '
         'stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<path class="ar-shaft" d="M3.5 12h13"/><path class="ar-head" d="m11.5 6.8 5.2 5.2-5.2 5.2"/>'
         '</svg>')


BPNAV = None  # parts/bpnav.py: the Big Picture row's list, set in main()


def nav_html(current, up, section=""):
    """The column's links. `current` is the page itself (aria-current="page");
    `section` is the row a page without a row of its own lives under (a
    document under My Research Areas, the CV under About Me, a post under
    Blog), marked the same way to the eye and as aria-current="true".

    His six topics (rows 5 to 10, the home page's topic cards) are not rows
    here: the Big Picture row's list names them (parts/bpnav.py), one item
    per category of the Big Picture page under its short name, each opening
    the page its row opened. On a topic's page, and on a document filed under
    a topic (From Bridges to Photons, under Waves and Dynamics), the Big
    Picture row is the section, the list opens with the page and marks the
    topic: "page" on its own page, "true" on the document. Without the part
    the row is a plain link, marked the same way, and its page lists them.

    A row with a sub-line is named by everything it shows, so what a reader
    sees is what a speech user says and a screen reader reads (WCAG 2.5.3).
    A colon no one sees joins the two, so the name reads "My Research Areas:
    Sound Waves, NDT, SHM" rather than running on."""
    items = []
    notes = BPNAV.notes() if BPNAV is not None and hasattr(BPNAV, "notes") else {}
    for _, label, pages in BPNAV.categories() if BPNAV is not None else ():
        page = next((h for h in TOPIC_ICONS if h in pages), pages[0])
        items.append((label, page, "page" if page == current else
                      "true" if current in pages else "", notes.get(label, "")))
    held = (current in TOPIC_ICONS and current not in OWN_ROW) or any(it[2] for it in items)
    section = "big-picture.html" if held else section
    out = []
    for href, title, sub, kind in NAV:
        if href in TOPIC_ICONS and href not in OWN_ROW:
            continue
        if href == current:
            on = ' class="on" aria-current="page"'
        elif href == section:
            on = ' class="on" aria-current="true"'
        else:
            on = ""
        if href == "big-picture.html" and BPNAV is not None:
            out.append(BPNAV.row(href, title, on, up, items,
                                 "here" if href == current else "in" if held else ""))
            continue
        grp = ' class="grp"' if kind == "group" else ""
        sub = (f'<span class="nav__sep">: </span><span class="nav__s">{sub}</span>'
               if sub else "")
        out.append(f'<li{grp}><a href="{up}{href}"{on}><span class="nav__t">{title}</span>'
                   f"{sub}</a></li>")
    return "".join(out)


# The fonts (DESIGN_BRIEF.md 2.1, plus the sans's 400 for the column's
# affiliation), served by the site itself (round-4 finding C7): the files
# Google Fonts serves for that request, split by script, kept in site/fonts/
# with their SIL Open Font License and copied to fonts/ by main().
# parts/theme.py declares them with font-display:swap, so a page never waits
# for them, and sizes the Georgia and Segoe UI that stand in until then.
# Every page preloads the two latin files its first screen needs; latin-ext
# and Greek load only on a page whose text uses them. No request leaves the
# site for a font, so no visitor's address goes to a font service.
FONT_DIR = os.path.join(SP, "fonts")
FONT_PRELOAD = ("source-serif-4-latin", "source-sans-3-latin")

# His portrait at the head of the column on every page and, small, in the
# phone's top bar (ROUND5_SPEC.md section 1): a square from his headshot,
# head and shoulders, which main() writes at each width a screen can ask for.
# The column draws it at 64px, 56px in a window 860px tall or less, and the
# bar at 32px; `sizes` says so, and the browser takes the file that covers
# that at its own density: 56 or 64 at one device pixel to the CSS pixel, 112
# or 128 at two, 168 at three (a phone's drawer).
PORTRAIT_SQ = (56, 64, 108, 112, 128, 168, 216)
# The square in headshot-708.png (708x691): 520px from the top edge, centred
# on his face (hair x 221-476, the middle at x=348), so the head is about two
# thirds of the frame, with 40px of wall over his hair and his collar in.
PORTRAIT_BOX = (88, 0, 608, 520)


def portrait(up, cls, size, alt=""):
    """His portrait as an <img>: `size` is the width the column (64, or 56 in a
    short window) or the phone bar (32) draws it at. The column's carries his
    name as its alt text; the bar's is empty, since his name is the words of
    the same link."""
    srcset = ", ".join(f"{up}portrait-sq-{w}.webp {w}w" for w in PORTRAIT_SQ)
    sizes = "(max-height: 860px) 56px, 108px" if size == 108 else f"{size}px"
    return (f'<img class="{cls}" src="{up}portrait-sq-64.webp" srcset="{srcset}" '
            f'sizes="{sizes}" width="{size}" height="{size}" alt="{alt}">')


# Each page's line for search results (<meta name="description">), ours, from
# what the page carries (round-4 finding C6: every page had the home page's).
# A document takes DOC_DESC, a post his opening sentence (lead()), a page in
# preparation his label and sub-line.
DESCRIPTION = ("Korkut Kaynardag, PhD. Structural health monitoring, nondestructive testing, "
               "wave propagation and machine learning.")
PAGE_DESC = {
    "presentation.html": "Korkut Kaynardag's presentation of his MSc and PhD research, in 177 slides.",
    "probability-statistics.html": ("Korkut Kaynardag's slides on probability, statistics and "
                                    "estimation: inference, uncertainty propagation, reliability, "
                                    "stochastic processes and Kalman filtering, in 74 slides."),
    "index.html": DESCRIPTION,
    "about.html": ("About Korkut Kaynardag, PhD, Assistant Professor in the Department of "
                   "Civil Engineering at Izmir Institute of Technology: his education, career "
                   "and research areas."),
    "cv.html": ("Curriculum vitae of Korkut Kaynardag, PhD: education, experience, grants, "
                "publications, patents and awards."),
    "research.html": ("Korkut Kaynardag's research areas: structural health monitoring (SHM), "
                      "non-destructive testing (NDT) and sound waves, with three documents "
                      "that introduce them."),
    "gallery.html": ("Field tests and instrumentation from Korkut Kaynardag's Ph.D. and M.Sc.: "
                     "rail measurements, laser Doppler vibrometry, bridges, a tall building, "
                     "a chimney, a wind turbine."),
    "big-picture.html": (f"{BIG_PICTURE}: waves, dynamics, signal processing, estimation, "
                         "optimization, machine learning and more, each with its guide."),
    "blog.html": ("Korkut Kaynardag's work that never made it into a paper: literature "
                  "reviews, methods and experiments from his research."),
    "contact.html": ("How to reach Korkut Kaynardag: Department of Civil Engineering, Izmir "
                     "Institute of Technology, Izmir, Turkiye."),
}
DOC_DESC = {
    SHORT: ("A two-page introduction to structural health monitoring (SHM) and "
            "non-destructive testing (NDT), by Korkut Kaynardag."),
    EXTENDED: ("A casual introduction to structural health monitoring and nondestructive "
               "testing, at length, by Korkut Kaynardag."),
    SOUND: ("Sound classification, localization and tracking, and their similarity to NDT: "
            "acoustic wave-based monitoring, by Korkut Kaynardag."),
    WAVES: ("Dynamical behavior of engineering structures and acoustic wave propagation: "
            "the vibrations and waves guide by Korkut Kaynardag."),
    SIGNAL: ("Signal processing, system identification, estimation theory and optimization, "
             "with the underlying logic of machine learning: a guide by Korkut Kaynardag."),
    ML: ("Machine learning, the complete picture: twelve sections, from what machine "
         "learning is to how to learn it, by Korkut Kaynardag."),
    PHOTONS: ("From bridges to photons: mode shapes and wave propagation in quantum "
              "mechanics, a short piece by Korkut Kaynardag."),
}


# Who built the site and drew its animations, at the foot of every page, at
# the professor's request (5 Oct 2026, his notes: 'Add "Site building and
# Animation creator" Muhammet ... somewhere you think will look cool'): a
# small wave, the site's own mark, drifting in the warm before the words, and
# the name's letters rising one after another, a wave passing through them,
# under the pointer. The name is said once, as text; the letters that move
# are a copy no screen reader reads.
CREDIT_WHAT, CREDIT_NAME = "Site building and animation creator", "Muhammet Yağcıoğlu"
CREDIT = (
    '<p class="foot__credit"><span class="credit">'
    '<svg class="credit__wave" viewBox="0 0 36 12" width="30" height="10" aria-hidden="true" '
    'focusable="false"><path d="M-24 6c3-5 6-5 9 0s6 5 9 0 6-5 9 0 6 5 9 0 6-5 9 0 6 5 9 0 6-5 9 0 6 5 9 0"/>'
    '</svg>'
    f'<span class="credit__what">{CREDIT_WHAT}</span><span class="credit__sep">: </span>'
    f'<span class="credit__name"><span class="credit__said">{CREDIT_NAME}</span>'
    '<span class="credit__shown" aria-hidden="true">'
    + "".join(f'<i style="--i:{k}">{"&nbsp;" if c == " " else c}</i>' for k, c in enumerate(CREDIT_NAME))
    + '</span></span></span></p>')


def soon_desc(href):
    """A page in preparation's line: his label and sub-line."""
    sub = next(s for h, _, s, _ in NAV if h == href)
    state = SOON_STATE.get(href, "In preparation")
    return (f"{nav_title(href)}: {sub}. {state}." if sub
            else f"{nav_title(href)}: {state[0].lower() + state[1:]}.")


# The tab's icon (the audit of 5 Oct 2026: a blank page icon in every tab and
# bookmark): the column's navy with a white wave, the site's mark, written
# into the page so it costs no request.
FAVICON = "data:image/svg+xml," + urllib.parse.quote(
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
    "<rect width='32' height='32' rx='7' fill='#043052'/>"
    "<path d='M4.5 16c2.9-6.2 5.1-6.2 8 0s5.1 6.2 8 0 4.4-6 7-1.2' fill='none' stroke='#fff' "
    "stroke-width='2.6' stroke-linecap='round'/></svg>", safe=":/='.,-")


def shell(current, title, body, depth=0, foot="", section="", head="", mast="", desc=""):
    """The page around `body`. `foot` adds a class to the footer: " foot--doc"
    on a document page, whose footer keeps to its column (parts/docs.py).
    `section` names the column row to mark on a page that has none of its
    own. `head` is markup for <head> that has to run before the first paint.
    `desc` is the page's line for search results, DESCRIPTION if it has none.

    The column's name block opens with his portrait, and the phone's top bar
    shows it small before his name (portrait()).

    `mast` is a band across the top of the page: the home page's masthead,
    his sentence on waves and data (parts/masthead.py). It opens <main>, so
    it spans the page from the column's edge to the window's and the column
    stays where it is on every page; on a phone it sits under the top bar
    (parts/theme.py, THE MASTHEAD). Inside <main> its words are in the page's
    landmark, and a <header> inside it is not a second banner."""
    up = "../" * depth
    top = f'<div class="mastrow">{mast}</div>\n' if mast else ""
    home = ' aria-current="page"' if current == "index.html" else ""
    # Above 1000px the reader can fold the column away (parts/theme.py, THE
    # FOLD). This script runs in <head>, ahead of the stylesheets and of the
    # first paint, and puts data-side="open" or "closed" on <html> from the
    # reader's last choice, so no page opens with the column only to slide it
    # away. A click on either .fold button flips the attribute, stores the
    # choice and hands focus to the button that stays on screen. Storage may be
    # missing or refuse (a private window, blocked site data): each call is in
    # try/catch and the column then opens, as on a first visit. Without
    # JavaScript nothing sets data-side, the buttons stay hidden and the column
    # stays open. A page restored from the back-forward cache picks up a choice
    # made on another page without replaying the slide (.side-still).
    # A pointer press that lands off the buttons within 500ms of a fold is
    # dropped (stray): it is the second half of a double-click, and the moving
    # column has just put the name, the link home, or the page's text under the
    # pointer. A keyboard click has detail 0 and always goes through. The script
    # also marks <html> "js", which shows the phone's menu button: without a
    # script the button could not open the drawer, and it is not drawn.
    fold_js = (
        '(function(d,h){var K="wad:sidebar",at=0;h.classList.add("js");'
        'function saved(){try{return localStorage.getItem(K)==="closed"?"closed":"open"}'
        'catch(e){return"open"}}'
        'function sync(){var o=h.getAttribute("data-side")==="closed"?"false":"true",'
        'b=d.querySelectorAll(".fold");for(var i=0;i<b.length;i++)b[i].setAttribute("aria-expanded",o)}'
        'function stray(e){return e.detail>0&&Date.now()-at<500&&'
        '!(e.target.closest&&e.target.closest(".fold"))}'
        'h.setAttribute("data-side",saved());'
        'd.addEventListener("DOMContentLoaded",sync);'
        'addEventListener("pageshow",function(e){var s=saved();'
        'if(!e.persisted||s===h.getAttribute("data-side"))return;'
        'h.classList.add("side-still");h.setAttribute("data-side",s);sync();'
        'requestAnimationFrame(function(){requestAnimationFrame(function(){'
        'h.classList.remove("side-still")})})});'
        'd.addEventListener("mousedown",function(e){if(stray(e))e.preventDefault()},true);'
        'd.addEventListener("click",function(e){'
        'if(stray(e)){e.preventDefault();e.stopPropagation();return}'
        'var b=e.target.closest&&e.target.closest(".fold");if(!b)return;at=Date.now();'
        'var shut=h.getAttribute("data-side")!=="closed";'
        'h.setAttribute("data-side",shut?"closed":"open");sync();'
        'try{if(shut)localStorage.setItem(K,"closed");else localStorage.removeItem(K)}catch(e){}'
        'if(d.activeElement===b){var t=d.querySelector(shut?".fold--show":".fold--hide");'
        'if(t)t.focus({preventScroll:true})}},true)'
        '})(document,document.documentElement);')
    # the fold buttons' glyph: a window with its sidebar pane, the inline icon
    # family (24-unit grid, drawn at 20px, stroke 1.5). The pane's edge is its
    # own path, so it can lean the way the column will go (parts/theme.py).
    panel = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
             'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
             '<rect x="3.25" y="4.75" width="17.5" height="14.5" rx="2.75"/>'
             '<path class="fold__edge" d="M9.25 4.75v14.5"/></svg>')
    # the title is both the tooltip and the button's name. Beside an aria-label
    # with the same words, Chrome exposed it a second time as the description.
    fold = 'type="button" aria-controls="site-nav" aria-expanded="true" title="{0}"'
    show, hide = fold.format("Show sidebar"), fold.format("Hide sidebar")
    fonts = "".join(f'<link rel="preload" href="{up}fonts/{f}.woff2" as="font" '
                    f'type="font/woff2" crossorigin>\n' for f in FONT_PRELOAD)
    # data-theme="light" is a decision: the client asked for a simple white/light
    # site, so the dark palette in parts/theme.py stays dormant. Drop the
    # attribute and the site follows the visitor's OS setting instead.
    bp_head = (f'<script id="bp-head">{BPNAV.head_js(current == "big-picture.html")}</script>'
               if BPNAV is not None else "")
    return f"""<!doctype html><html lang="en" data-theme="light"><meta charset="utf-8">
<title>{title}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script>{fold_js}</script>{bp_head}{head}
<link rel="icon" href="{FAVICON}">
<meta name="description" content="{html.escape(desc or DESCRIPTION)}">
{fonts}<link rel="stylesheet" href="{up}style.css">
<link rel="stylesheet" href="{up}parts.css">
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="bar">
  <a class="bar__id" href="{up}index.html"{home}>{portrait(up, "bar__pic", 32)}Korkut Kaynardag</a>
  <button class="burger" type="button" aria-label="Menu" aria-controls="site-nav" aria-expanded="false"><i></i><i></i><i></i></button>
</header>
<div id="scrim" aria-hidden="true"></div>
<button class="fold fold--show" {show}>{panel}</button>
<nav class="side" id="site-nav" aria-label="Site">
  <a class="id" href="{up}index.html" aria-label="Korkut Kaynardag, home"{home}>
    {portrait(up, "id__pic", 108, "Korkut Kaynardag")}
    <b>Korkut Kaynardag</b>
    <span class="id__role">PhD, Assistant Professor</span>
    <span class="id__org">Department of Civil Engineering<br>Izmir Institute of Technology</span>
  </a>
  <button class="fold fold--hide" {hide}>{panel}</button>
  <ul class="nav">{nav_html(current, up, section)}</ul>
  <div class="side__end"></div>
</nav>
<div class="main">
<main id="main">
{top}{body}
</main>
<footer class="foot{foot}">
  <p><b>Korkut Kaynardag, PhD</b><br>
  Assistant Professor, <span class="nw">Department of Civil Engineering</span><br>
  Izmir Institute of Technology, Izmir, Turkiye<br>
  <a class="foot__mail" href="mailto:{CONTACT['personal']}">{CONTACT['personal']}</a></p>
  <nav aria-label="Footer">
    <a href="{up}about.html">About</a><a href="{up}research.html">Research</a>
    <a href="{up}gallery.html">Gallery</a><a href="{up}big-picture.html">Big Picture</a>
    <a href="{up}blog.html">Blog</a><a href="{up}communication.html">Communication</a>
    <a href="{up}personal-advices.html">Personal Advices</a><a href="{up}contact.html">Contact</a>
  </nav>
  {CREDIT}
</footer>
</div>
<script src="{up}parts.js" defer></script>
</body></html>
"""


# ------------------------------------------------ what the em dash report reads

DASH = re.compile("\u2014|&mdash;|&#8212;|&#x2014;", re.I)
SPACED_EN = re.compile(" (?:\u2013|&ndash;|&#8211;|&#x2013;) ", re.I)
OWNED = []      # (file, fragment): markup a part rendered, so a dash is billed to it
VERBATIM = [PROF_HEADER, PROF_INTRO, PROF_BIO, PROF_MOTIVATION, PROF_ABOUT, PROF_RESEARCH,
            PROF_RESEARCH_MORE]   # his words; his converted documents join below


def mine(owner, fragment):
    """Record a fragment a part rendered, then hand it back."""
    if fragment:
        OWNED.append((owner, fragment))
    return fragment


# ---------------------------------------------------------------- doc pages

# The picture files a document page draws. Each is written once, after the
# pages, the way the pages use it (preview.USAGE): a figure is flattened onto
# white and capped at WEB_MAX pixels wide, with a WEB_SMALL copy beside it for
# a screen that does not need the full file; a picture in a table, a row of
# steps or a sentence keeps its transparent ground and is drawn bare.
#
# 1344 is the column (672px, --measure-doc) at two device pixels to the CSS
# pixel, so a figure the column's width is sharp on a retina screen; 1280 left
# it at 1.9. 720 covers the column at one pixel to the point and every phone
# column (346px at 390, 276 at 320) at two.
WEB_MAX, WEB_SMALL = 1344, 720
NARROW = 0.8     # below this share of Word's column the author set a picture narrow
FLOOR = 0.6      # and it is drawn at this share of the column at least


def measure_px():
    """--measure-doc from parts/theme.py: the document column every figure,
    table and caption shares, so the sizes below have one source."""
    try:
        from parts import theme
        m = re.search(r"--measure-doc:\s*(\d+)px", theme.CSS)
        return int(m.group(1)) if m else 672
    except ImportError:
        return 672


def web_size(w, h, cap=WEB_MAX):
    """The size of a picture's WebP: its own, or `cap` wide if it is wider."""
    return (w, h) if w <= cap else (cap, max(1, round(h * cap / w)))


def figure_meta(slug, nodes):
    """build.py's word on every picture of a document, by IMAGE node id: its
    files and their size, how much of the column it takes, and whether it sat
    in a sentence - for preview.py to draw it by.

    The share of the column is the author's: the width Word draws the picture
    at over the width of Word's text column, both from the converter's
    manifest (tools/ricos, word_width and text_width). The manifest lists the
    figures in the order the nodes hold them; a filename that disagrees stops
    the pairing rather than giving one picture another's size.
    """
    path = os.path.join(BUILD, slug, "manifest.json")
    manifest = json.load(open(path, encoding="utf-8")) if os.path.isfile(path) else {}
    figures = manifest.get("figures", [])
    column = manifest.get("text_width") or 0
    measure = measure_px()
    images = []

    def walk(ns):
        for n in ns:
            if n.get("type") == "IMAGE":
                images.append(n)
            walk(n.get("nodes", []))

    walk(nodes)
    meta = {}
    for node, fig in zip(images, figures, strict=False):
        img = node["imageData"]["image"]
        name = img["src"]["id"]
        if fig.get("filename") != name:
            print(f"  !! doc/{slug}.html: manifest and part disagree at {name}; "
                  f"pictures from here on take their plain size")
            break
        stem = os.path.splitext(name)[0]
        w, h = web_size(img.get("width") or 0, img.get("height") or 0)
        share = fig["word_width"] / column if column and fig.get("word_width") else 1.0
        inset = max(FLOOR, share) if share < NARROW else 1.0
        shown = min(w, round(inset * measure))
        m = {"src": f"../fig/{slug}/{stem}.webp", "w": w, "h": h,
             "zoom": w >= 480 and w > shown * 0.9,
             "sizes": (f"(max-width: 640px) calc(100vw - 44px), {round(inset * measure)}px"
                       if inset < 1 else
                       f"(max-width: {measure + 44}px) calc(100vw - 44px), {measure}px")}
        if inset < 1 and w > round(inset * measure):
            m["inset"] = round(inset * 100, 1)
        if (img.get("width") or 0) > WEB_SMALL:
            m["src720"] = f"../fig/{slug}/{stem}-{WEB_SMALL}.webp"
        for key in ("inline", "offset", "joins"):
            if key in fig:
                m[key] = fig[key]
        meta[node["id"]] = m
    return meta


# Words cut from his text on the site, each with its reason; doc_body() stops
# the build if one is no longer there, once, to cut. Figure 4 of the waves
# guide is drawn on the site from a SAFE model (tools/numfig/dispersion.py),
# so its note that an AI made the figure no longer holds here; the Word file
# keeps the old figure and the note with it (the user, 26 Sep 2026: "evet
# çıkar").
CUTS = {
    "dynamical-behavior-of-engineering-structures-and-acoustic-wave-propagation": (
        " (This figure is created by AI, and it is representative, but you will see very "
        "similar dispersion and cross-sectional deformation figures once you check the real "
        "wave propagation analysis results.)",),
}


# Alt text for the pictures whose content nothing else on the page carries: an
# equation he set as an image (it appears twice, once inside Figure 5), and the
# brochure's four labelled diagrams, which have no captions. The words describe
# his pictures; the pictures are unchanged. The minus is U+2212.
ALT = {
    "dynamical-behavior-of-engineering-structures-and-acoustic-wave-propagation": {
        "image16": "u(x, y, z, t) = U(y, z) e^(i(kx \u2212 \u03c9t))",
    },
    "brochure-shm-and-ndt-2-pages": {
        "image5": "Diagram: the vibration of a structure, picked up by sensors along its "
                  "height, is the sum of its 1st vibration mode shape and frequency, its 2nd "
                  "vibration mode shape and frequency, and higher modes.",
        "image6": "Diagram: acoustic emission. A sensor on a steel beam is only listening, "
                  "and waves spread from a defect in the beam.",
        "image7": "Diagram: an acoustic sensor on a steel beam sends waves and receives their "
                  "reflections from a crack. The recorded signal plots amplitude against "
                  "time, with peaks for the excitation, the reflection and the boundary.",
        "image8": "Diagram: an array of scanning transducers on a structure fires one element "
                  "after another, and waves reflect from a crack inside it. The resulting image "
                  "shows the crack.",
    },
}

# His animated figures, each in place of the picture it redraws, by document
# and picture (preview.animations()); main() fills it as it publishes them.
ANIM = {}
ANIM_ASSETS = (".webp", ".png", ".json", ".bin")   # an nf- figure's frame and data


# A figure he asked to follow the text it belongs to (29 Sep 2026: "NDT SHM
# sectionlarina figureler yazinin altinda olmasi gerek"): each figure, found by
# the start of its caption, moves to just after the paragraph that starts with
# the given words, the section's closing paragraph. His words and figures are
# unchanged; each must be found exactly once or the build stops.
FIGURE_AFTER = {
    "understanding-shm-and-ndt": [
        ("Figure 2. OMA and EMA workflow.", "Within the SHM and NDT field"),
        ("Figure 3. NDT:", "Accordingly, this second broad approach"),
    ],
}

# A link he did not set in Word, where his words point at a page of this site
# (29 Sep 2026: the multi-objective optimization mention goes to the blog post):
# (his sentence, the words in it that carry the link, where it goes). His words
# stay as they are; the sentence must be found exactly once.
DOC_LINKS = {
    "signal-processing-system-identification-and-optimization": [
        ("Please see my blog for more on multi-objective optimization", "my blog",
         "../post/multi-objective-optimization.html"),
    ],
}


def _words_of(markup):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", markup)).split())


def place_figures(body, slug):
    """FIGURE_AFTER for one document."""
    for cap, after in FIGURE_AFTER.get(slug, ()):
        figs = [m for m in re.finditer(r"<figure\b.*?</figure>", body, re.S)
                if _words_of((re.search(r"<figcaption>(.*?)</figcaption>", m.group(0), re.S)
                              or re.match("(.*)", "")).group(1)).startswith(cap)]
        if len(figs) != 1:
            sys.exit(f"doc/{slug}.html: FIGURE_AFTER finds {len(figs)} figures captioned {cap!r}")
        fig = figs[0].group(0)
        body = body[:figs[0].start()] + body[figs[0].end():]
        paras = [m for m in re.finditer(r"<p\b[^>]*>.*?</p>", body, re.S)
                 if _words_of(m.group(0)).startswith(after)]
        if len(paras) != 1:
            sys.exit(f"doc/{slug}.html: FIGURE_AFTER finds {len(paras)} paragraphs starting {after!r}")
        body = body[:paras[0].end()] + fig + body[paras[0].end():]
    return body


def link_words(body, slug):
    """DOC_LINKS for one document."""
    for sentence, words, href in DOC_LINKS.get(slug, ()):
        if body.count(sentence) != 1 or words not in sentence:
            sys.exit(f"doc/{slug}.html: DOC_LINKS finds {body.count(sentence)} of {sentence!r}")
        linked = sentence.replace(words, f'<a class="inlink" href="{href}">{words}</a>', 1)
        body = body.replace(sentence, linked)
    return body


ADDITIONS = os.path.join(ROOT, "content", "additions")


def _anchor(body, slug, spec, what):
    """Where an addition goes: (start, end) of the one element its anchor
    names, and whether it goes before that element rather than after it.

    after_caption: the figure whose caption starts with the words;
    after_paragraph / before_paragraph: the paragraph that starts with them;
    after_list_containing: the list that holds them; after_heading: the h2 or
    h3 whose words are exactly these (the addition opens the section), of
    `level` 2 or 3 where the words head both. An anchor found other than once
    stops the build."""
    if "after_caption" in spec:
        matches = [m for m in re.finditer(r"<figure\b.*?</figure>", body, re.S)
                   if (cap := re.search(r"<figcaption>(.*?)</figcaption>", m.group(0), re.S))
                   and _words_of(cap.group(1)).startswith(spec["after_caption"])]
    elif "after_paragraph" in spec or "before_paragraph" in spec:
        words = spec.get("after_paragraph") or spec["before_paragraph"]
        matches = [m for m in re.finditer(r"<p\b[^>]*>.*?</p>", body, re.S)
                   if _words_of(m.group(0)).startswith(words)]
    elif "after_heading" in spec:
        matches = [m for m in re.finditer(r"<h([23])\b[^>]*>(.*?)</h\1>", body, re.S)
                   if _words_of(m.group(2)) == spec["after_heading"]
                   and str(spec.get("level", m.group(1))) == m.group(1)]
    else:
        matches = [m for m in re.finditer(r"<ul\b[^>]*>.*?</ul>", body, re.S)
                   if spec["after_list_containing"] in _words_of(m.group(0))]
    if len(matches) != 1:
        sys.exit(f"doc/{slug}.html: supplement {what} finds {len(matches)} anchors")
    return matches[0].start(), matches[0].end(), "before_paragraph" in spec


# A number and its unit stay on one line in the words we add (the audit of
# 5 Oct 2026 found "4" at a line's end and "s" starting the next): the space
# between them becomes a no-break space, outside the formulas.
_UNIT = re.compile(r"(\d)[ ]((?:k|M)?Hz|dB|ms|µs|s|mm|cm|km|m|MN/m|MN|kN|GPa|MPa|kg|t"
                   r"|degrees|deg|samples|shots|elements|iterations)(?![\w/])")


def nbsp_units(text):
    """`text` with each number's space before its unit made a no-break space,
    leaving <tex> formulas and tags alone."""
    parts = re.split(r"(<tex[^>]*>.*?</tex>|<[^>]+>)", text, flags=re.S)
    return "".join(p if i % 2 else _UNIT.sub("\\1\u00a0\\2", p) for i, p in enumerate(parts))


def _added_text(slug, name):
    """One block of new text for a guide, content/additions/<name>: paragraphs
    (and an h3 where a section's new part needs one) with <tex>TeX</tex>
    formulas set as the documents' formulas are (mathtex.typed()). The words
    are ours, written for him, so the build holds them to the site's own
    rules: no em dash and no spaced en dash, and only the tags a passage of
    his document uses."""
    path = os.path.join(ADDITIONS, name)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    where = os.path.relpath(path, ROOT).replace(os.sep, "/")
    if DASH.search(text) or SPACED_EN.search(text):
        sys.exit(f"{where}: an em dash or a spaced en dash")
    tags = set(re.findall(r"</?([a-zA-Z][\w-]*)", text)) - {"p", "h3", "em", "i", "b", "strong",
                                                             "a", "tex", "sub", "sup", "ul", "li"}
    if tags:
        sys.exit(f"{where}: tags a passage of his does not use: {sorted(tags)}")
    import mathtex
    return mathtex.typed(nbsp_units(text.strip()), where)


def add_supplementary_figures(body, slug):
    """Numerical examples, and the words that go with them, added to the guides
    without changing their Word source (content/anim/supplements.json).

    Each entry is a figure (`key`, from the animation manifest, with its
    `caption`) or a block of new text (`html`, a file in content/additions/),
    put in place by its anchor (_anchor()) in the order listed; a figure
    marked `in_text` has no anchor and stands where a block of text marks it
    (<!--figure:key-->), each such figure marked exactly once. Anchors must
    match once. Assets use the ordinary animation manifest, so full screen,
    no-script, print, lazy loading and publishing stay shared.
    """
    path = os.path.join(ROOT, "content", "anim", "supplements.json")
    if not os.path.isfile(path):
        return body
    with open(path, encoding="utf-8") as fh:
        supplements = json.load(fh).get(slug, [])
    numbers = {}
    if isinstance(supplements, dict):   # {"renumber": {his: page's}, "add": [entries]}
        numbers, supplements = supplements.get("renumber", {}), supplements["add"]
    import preview

    def figure(spec):
        """A figure entry drawn, or "" where the page is drawn without its
        animations (page_doc also renders the original without them)."""
        anim = ANIM.get(slug, {}).get(spec["key"])
        if anim is None:
            return ""
        still = anim.get("still")
        if not still:
            sys.exit(f"doc/{slug}.html: supplement {spec['key']} has no printed frame")
        image = (f'src="{html.escape(still["src"])}" width="{still["w"]}" '
                 f'height="{still["h"]}" alt="{html.escape(anim["title"])}"')
        # a caption is plain text, but for a subscript or superscript (ACO<sub>R</sub>)
        cap = re.sub(r"&lt;(/?)(sub|sup)&gt;", r"<\1\2>", html.escape(nbsp_units(spec["caption"])))
        return preview._animated(anim, image, f'<figcaption>{preview._figno(cap)}</figcaption>')

    # a figure "in_text" stands where a block of new text marks it,
    # <!--figure:key-->, so a new passage reads as one: its paragraphs, its
    # figures among them, in the order written
    held = {spec["key"]: figure(spec) for spec in supplements if spec.get("in_text")}
    body = renumber(body, numbers)
    for spec in supplements:
        if spec.get("in_text"):
            continue
        if "html" in spec:
            what = spec["html"]
            piece = _added_text(slug, what)

            def place(m):
                if m.group(1) not in held:
                    sys.exit(f"doc/{slug}.html: {what} marks a figure no entry holds: {m.group(1)}")
                return held.pop(m.group(1))

            piece = re.sub(r"<!--figure:([\w-]+)-->", place, piece)
        else:
            what = spec["key"]
            piece = figure(spec)
            if not piece:
                continue
        start, end, before = _anchor(body, slug, spec, what)
        at = start if before else end
        body = body[:at] + piece + body[at:]
    if held:
        sys.exit(f"doc/{slug}.html: figures no text marks: {sorted(held)}")
    return numbered_in_turn(body, slug) if numbers else body


def renumber(body, numbers):
    """A document whose figures are numbered again because figures were added
    among his own (supplements.json, "renumber": his number -> the page's;
    the signal processing guide, 5 Oct 2026: his Figure 2 is the page's 3,
    his Figure 3 its 8). Before the additions go in, each "Figure N" of his,
    in a caption or in his text, takes the page's number, all in one pass,
    so 2 becoming 3 never meets 3 becoming 8. The added figures' captions and
    words carry the page's numbers already."""
    if not numbers:
        return body
    return re.sub(r"(\bFigures? )(\d+)(?![\w])",
                  lambda m: m.group(1) + numbers.get(m.group(2), m.group(2)), body)


def numbered_in_turn(body, slug):
    """After the additions, a renumbered document's captions must read 1, 2,
    3... down the page, and every "Figure N" in it must name one of them;
    anything else stops the build. A page drawn without the animations (no
    ANIM for it, as some tests draw one) has no added figures to count."""
    if not ANIM.get(slug):
        return body
    caps = re.findall(r'<figcaption><span class="fign">Figure (\d+[a-z]?)\.</span>', body)
    if caps != [str(k) for k in range(1, len(caps) + 1)]:
        sys.exit(f"doc/{slug}.html: the figures do not read 1, 2, 3... in turn: {caps}")
    named = set(re.findall(r"\bFigures? (\d+[a-z]?)(?![\w])", body)) - set(caps)
    if named:
        sys.exit(f"doc/{slug}.html: the text names figures the page does not have: {sorted(named)}")
    return body


def still_alt(body):
    """A moving figure's still whose picture had no alt text in his Word file
    (and none in ALT) takes the frame's title, so paper and a page without
    script still say what it shows (the cover and Figures 1, 3 and 8 of the
    signal guide had none). A table's cell keeps its empty alt, its label
    standing beside it."""
    return re.sub(r'(<figure class="fig--anim"><iframe class="anim" [^>]*?title="([^"]*)"'
                  r'(?:(?!</figure>).)*?<img class="anim__still" [^>]*?)alt=""',
                  lambda m: f'{m.group(1)}alt="{m.group(2)}"', body, flags=re.S)


def doc_body(slug):
    with open(os.path.join(BUILD, slug, "part-01.json"), encoding="utf-8") as fh:
        doc = json.load(fh)
    body = "".join(render(n, f"../fig/{slug}") for n in doc["nodes"])
    body = re.sub(r'(src="\.\./fig/[^"]+)\.(?:png|jpe?g|gif|bmp|tiff?)"', r'\1.webp"', body,
                  flags=re.I)
    for name, text in ALT.get(slug, {}).items():
        # a picture redrawn as a moving figure hands its words to the frame
        # that figure prints (nf-<name>.webp), which stands where it stood
        moved = ANIM.get(slug, {}).get(name, {})
        if isinstance(moved, list):      # a picture redrawn as several figures: the first prints it
            moved = moved[0]
        still = moved.get("still", {}).get("src", "")
        stem = still.rsplit("/", 1)[-1][:-len(".webp")] if still.endswith(".webp") else name
        was = f'/{stem}.webp" alt=""'
        if was not in body:
            sys.exit(f"doc/{slug}.html: no {stem} with empty alt text to describe")
        body = body.replace(was, f'/{stem}.webp" alt="{html.escape(text)}"')
    body = still_alt(body)
    for cut in CUTS.get(slug, ()):
        if body.count(cut) != 1:
            sys.exit(f"doc/{slug}.html: the words to cut are not there once: {cut[:60]!r}")
        body = body.replace(cut, "")
    measure = measure_px()

    # Small uncaptioned images that follow one another and fit the column side
    # by side were set side by side in Word (the book covers his captions read
    # "Left to right"), so they share a row here instead of stacking. Word
    # draws every cover in a row at one height (175px); the row is set to the
    # shortest cover's own height, so none is enlarged, and each cover takes
    # the share of the row its proportions ask for, so the heights stay equal
    # as the row narrows on a phone.
    def row(m):
        sizes = [(int(w), int(h)) for w, h in
                 re.findall(r' width="(\d+)" height="(\d+)"', m.group(0))]
        if not sizes or sum(w for w, _ in sizes) + 20 * (len(sizes) - 1) > measure:
            return m.group(0)
        height = min(h for _, h in sizes)
        ratios = [w / h for w, h in sizes]
        figs = iter(ratios)
        inner = re.sub(r"<figure>", lambda _: f'<figure style="flex-grow:{next(figs):.4f}">',
                       m.group(0).strip())
        # the covers' width at that height; the gaps are the stylesheet's
        return (f'<div class="figrow" style="--rw:{sum(ratios) * height:.1f}px;'
                f'--gaps:{len(sizes) - 1}">{inner}</div>')

    body = re.sub(r"(?:<figure><img [^>]*></figure>\s*){2,}", row, body)
    # His personal Gmail closes three guides' disclaimers ("...a section of this
    # document: korkut.kaynardag@gmail.com"). Since 29 Sep 2026 it is public for
    # contact, so his sentence keeps his own address, as a link that writes to
    # him. Any address but his two public ones stops the build.
    mail = CONTACT["personal"]
    body = re.sub(r"korkut\.kaynardag@gmail\.com", f'<a href="mailto:{mail}">{mail}</a>', body,
                  flags=re.I)
    other = {a.rstrip(".") for a in re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", body)} - PUBLIC_EMAILS
    if other:
        sys.exit(f"doc/{slug}.html: an address the site must not carry: {sorted(other)}")
    return add_supplementary_figures(link_words(place_figures(body, slug), slug), slug)


def page_doc(slug, word=None, pending=False):
    """One document page, doc/<slug>.html. word = (file, bytes, his file name)
    when its Word original ships as doc/<file>; pending when it is one of the
    hosted Word files and this build publishes none (--no-word): the line
    then waits, in the research boxes' words.

    His own cover (picture, title, subtitle, byline) is the page's header, so
    the title is his and is said once; the link above it says where
    the page lives. Text, pictures, tables and captions share one column,
    672px (--measure-doc), centred in the space the site's column leaves.

    A document long enough to lose your place in (three sections and 1,000
    words or more) gets its contents in the text, where his "Table of
    Contents" line stood or else under the header, as a <details open> the
    reader can fold. With the script there is also a dock (parts/docs.py
    has the whole system): one quiet Contents button beside the column, and
    the list it opens - in the margin where the margin holds it, over the
    text where it does not, from the foot of the screen on a phone. Shut,
    only the button is left. The script in <head> puts the reader's last
    choice on <html> before the page paints, so a list closed on one
    document opens closed on the next. The download reads as it does under
    the research boxes (parts/rboxes.py): the same mark, the same words, the
    size in decimal MB.
    """
    import preview
    title = DOCS[slug][0]
    with open(os.path.join(BUILD, slug, "part-01.json"), encoding="utf-8") as fh:
        nodes = json.load(fh)["nodes"]
    words = sum(len(preview._text(n).split()) for n in nodes)
    preview.plan(nodes, figure_meta(slug, nodes), ANIM.get(slug))
    try:
        cover, body = preview.head(doc_body(slug))
        label = preview._PLAN["toc"]
    finally:
        preview.plan([])
    body, sections = preview.outline(preview.zoom(preview.captions(body)))
    body = preview.regions(body)
    cover = cover or f"<h1>{title.replace(' / ', '&nbsp;/ ')}</h1>"

    chapters = [s for s in sections if s[1] == 2]
    toc = len(chapters) >= 3 and words >= 1000
    name = html.escape(label or "Contents")
    dock = head = ""
    if toc:
        # The summary row: his label and the chevron that turns as the list
        # folds. Shut, the list in the text says how many sections it holds.
        chev = ('<svg class="toc__chev" viewBox="0 0 24 24" width="18" height="18" fill="none" '
                'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
                'stroke-linejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>')
        lis = "".join(f'<li><a href="#{sid}">{inner}</a></li>' for sid, _, inner, _ in chapters)
        in_text = (f'<nav class="toc toc--body" id="contents" aria-labelledby="toc-h">'
                   f'<details class="toc__fold" open><summary class="toc__sum">'
                   f'<span class="toc__h" id="toc-h">{name}</span>{chev}'
                   f'<span class="toc__n" aria-hidden="true">{len(chapters)} sections</span>'
                   f'</summary><ol>{lis}</ol></details></nav>')
        tree = []
        for sid, level, inner, _ in sections:
            if level == 2:
                tree.append([f'<a href="#{sid}">{inner}</a>', []])
            elif tree:
                tree[-1][1].append(f'<li><a href="#{sid}">{inner}</a></li>')
        items = "".join(f'<li>{a}<ol>{"".join(sub)}</ol></li>' if sub else f"<li>{a}</li>"
                        for a, sub in tree)
        # The dock: the button that stays, and the list it opens. The button
        # says what it holds in a word ("Contents"); the list keeps his own
        # label. The x closes the list where it lies over the text.
        icon = ('<svg class="tocbtn__i" viewBox="0 0 24 24" width="20" height="20" fill="none" '
                'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
                'stroke-linejoin="round" aria-hidden="true">'
                '<path d="M9 6.5h11M9 12h11M9 17.5h11M4.5 6.5h.01M4.5 12h.01M4.5 17.5h.01"/></svg>')
        close = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
                 'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" '
                 'aria-hidden="true"><path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/></svg>')
        dock = (f'<div class="tocdock">'
                f'<button class="tocbtn" type="button" aria-controls="toc-panel" '
                f'aria-expanded="false">{icon}<span class="tocbtn__t">Contents</span></button>'
                f'<nav class="toc toc--rail tocpanel" id="toc-panel" aria-labelledby="toc-r">'
                f'<div class="tocpanel__head"><span class="toc__h" id="toc-r">{name}</span>'
                f'<button class="tocpanel__x" type="button" aria-label="Close contents">'
                f'{close}</button></div>'
                f'<div class="toc__track"><ol class="toc__list">{items}</ol>'
                f'<span class="toc__mark" aria-hidden="true"></span></div></nav></div>'
                f'<div class="tocscrim" aria-hidden="true"></div>')
        # before the first paint: the reader's last choice, or open (docs.py)
        head = ('<script>try{var t=localStorage.getItem("wad:toc")}catch(e){}'
                'document.documentElement.setAttribute("data-toc",'
                't==="closed"?"closed":"open")</script>')
        VERBATIM.extend(inner for _, _, inner, _ in sections)   # the lists repeat his headings
        if "<!--toc-->" in body:
            body, in_text = body.replace("<!--toc-->", in_text, 1), ""
    else:
        in_text = ""
        body = body.replace("<!--toc-->", f"<p>{name}</p>" if label else "")
    VERBATIM.extend([body, cover])

    get = ""
    if word:
        get = (f'<p class="docmeta"><a class="docdl" href="{word[0]}" '
               f'download="{html.escape(word[2])}">'
               f'{svg("download")}<span class="docdl__t">Download Word</span> '
               f'<span class="docdl__size">{word[1] / 1e6:.2f}&nbsp;MB</span></a></p>')
    elif pending:
        get = (f'<p class="docmeta"><span class="docdl docdl--wait">{svg("download")}'
               f'<span>Word file, coming soon</span></span></p>')

    def plain(pattern):
        m = re.search(pattern, cover, re.S)
        return " ".join(html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).split()) if m else ""

    h1 = plain(r"<h1>(.*?)</h1>")
    if h1 and h1 != " ".join(title.split()):
        print(f"  !! build.py DOCS[{slug!r}] says {title!r}, but the page opens with "
              f"{h1!r}; give DOCS the page's title")
    long = " dochead--long" if len(h1) > 64 else ""
    # The tab carries his title too. His machine learning guide's cover title is
    # "Machine Learning", which is also the topic page's name, so where he set a
    # running line above the title ("Machine Learning: The Complete Picture")
    # the tab takes that line instead.
    tab = plain(r'<p class="dochead__pre">(.*?)</p>') or h1 or title
    VERBATIM.append(html.escape(tab, quote=False))
    inner = f"""<div class="wrap docpage{' has-toc' if toc else ''}">
  {doc_crumb(slug)}
  {dock}
  <article class="docart">
  <header class="dochead{long}">{cover}{get}</header>
  {in_text}
  <div class="doc">{body}</div>
  </article>
</div>"""
    return shell(f"doc/{slug}.html", html.escape(tab, quote=False) + " · Korkut Kaynardag",
                 inner, depth=1, foot=" foot--doc", section=doc_section(slug), head=head,
                 desc=DOC_DESC.get(slug) or f"{tab}.")


def doc_crumb(slug):
    """The link above a document's title, back to the row it lives under
    (DOC_HOME): My Research Areas for the three SHM and NDT documents, the Big
    Picture for the rest."""
    home = DOC_HOME[slug]
    if not home:
        return ""
    back = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
            'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true"><path d="m14.5 6-6 6 6 6"/></svg>')
    return (f'<nav class="crumb" aria-label="Breadcrumb"><a href="../{home}">{back}'
            f'{html.escape(nav_title(home), quote=False)}</a></nav>')


def nav_title(href):
    """The column's title for a row, as plain text."""
    return next(t for h, t, _, _ in NAV if h == href).replace("\u00a0", " ")


def doc_section(slug):
    """The row a document marks as its section, the row of the page it lives
    under. None for his three guides, NAV's topic rows: nav_html() marks the
    Big Picture row for them, as for every topic's page."""
    if any(h == f"doc/{slug}.html" for h, _, _, _ in NAV):
        return ""
    return DOC_HOME[slug] or ""


# ---------------------------------------------------------------- nav pages
#
# Every page's body comes from its part (design/ROUND4_SPEC.md section 10),
# through call(). While a part is missing, or has not caught up with its
# interface yet, the page is built from the plain fallback here instead: every
# link live and his words whole, so no build ships a hole.

def box(slug, icon, label, word=None):
    """Fallback research box, used only while parts/rboxes.py is missing."""
    ic = f'<img src="icon/{icon}" alt="" width="56" height="56">' if icon else ""
    dl = (f'<a class="dl" href="doc/{word[0]}" download="{html.escape(word[2])}">'
          f'Download Word</a>' if word
          else '<span class="dl off">Word file being prepared</span>')
    return f'<div><a class="box" href="doc/{slug}.html"><b>{label}</b>{ic}</a>{dl}</div>'


HERO_FALLBACK = f""" <div class="hero">
  <div>
   <h1>Korkut Kaynardag, PhD</h1>
   {PROF_INTRO}
   {PROF_BIO}
   <p><a class="btn" href="about.html">About Me</a></p>
  </div>
  <img src="portrait.webp" srcset="portrait-280.webp 280w, portrait.webp 520w" sizes="280px"
       alt="Korkut Kaynardag" width="520" height="650">
 </div>
"""


# The band across the top of the home page while parts/masthead.py is missing:
# his sentence, plainly set. parts/theme.py places the band.
MAST_FALLBACK = f'<div class="mastfb"><p>{PROF_HEADER}</p></div>'


def ready(mod, name, *args, **kw):
    """Call a part's `name` with the arguments of its interface and return
    what it renders; None while the part is missing, has no such function, or
    does not take those arguments yet. Its page is then built from the
    fallback here, never from a render that would drop his words or link a
    page that is gone."""
    f = getattr(mod, name, None) if mod else None
    if f is None:
        return None
    try:
        inspect.signature(f).bind(*args, **kw)
    except TypeError as e:
        print(f"  !! parts/{mod.__name__.rsplit('.', 1)[-1]}.py: {name}() does not take "
              f"its interface yet ({e}); the page is built from build.py's fallback")
        return None
    return f(*args, **kw)


def wrap_page(title, body):
    """A page body as a part renders it, in the site's .wrap and under its
    <h1>: a part that writes either itself keeps its own."""
    m = re.match(r'\s*<div class="wrap\b[^"]*">', body)
    if "<h1" not in body:
        body = (f"{body[:m.end()]}\n <h1>{title}</h1>\n{body[m.end():]}" if m
                else f"<h1>{title}</h1>\n{body}")
    return body if m else f'<div class="wrap">\n{body}\n</div>'


def topic_items():
    """The home page's six topic cards, rows 5 to 10 of the column in its
    order, as parts/topics.py takes them: the row's href, title and sub-line,
    the subject its icon draws, and whether its page is in preparation."""
    return [{"href": href, "title": title, "sub": sub, "icon": TOPIC_ICONS[href],
             "soon": href in SOON} for href, title, sub, _ in NAV if href in TOPIC_ICONS]


def page_home(hero_html=None, topics_html=None, middle_html=None):
    if not topics_html:
        cards = "".join(
            f'<a class="box" href="{t["href"]}"><b>{t["title"]}</b>'
            + (f'<em>{t["sub"]}</em>' if t["sub"] else "")
            + ('<em class="soon">In preparation</em>' if t["soon"] else "") + "</a>"
            for t in topic_items())
        topics_html = f'\n <h2>Explore the topics</h2>\n <div class="boxes">{cards}</div>'
    return (f'<div class="wrap">\n{hero_html or HERO_FALLBACK}\n'
            + (middle_html or PROF_MOTIVATION) + topics_html + "\n</div>")


# His career, for the About page's fallback while no timeline part loads.
CAREER = (("Since 2026", "Assistant Professor",
           "Department of Civil Engineering, Izmir Institute of Technology",
           "Structural health monitoring, nondestructive damage detection, smart sensors and "
           "smart cities. Since August 27, 2026."),
          ("2024&#8211;2026", "Senior AI Engineer", "Renesas Electronics America, Maryland, USA",
           "Acoustic wave-based vehicle monitoring; sound source tracking."),
          ("2023&#8211;2024", "Applied Data Scientist",
           "Transtek International Group, Florida, USA",
           "Bridge and road monitoring solutions."),
          ("2016&#8211;2023", "Ph.D. &amp; Graduate Research Assistant",
           "The University of Texas at Austin, Texas, USA",
           "Product- and service-oriented research on structural health monitoring and "
           "non-destructive testing systems."),
          ("2013&#8211;2016", "M.Sc., Project &amp; Research Assistant",
           "Bogazici University, Istanbul, Turkey",
           "Structural health monitoring and non-destructive testing systems. "
           "B.Sc. in Civil Engineering, 2013."))


def page_about(timeline_html=None, links=(), areas=(), glance_html=""):
    """About Me (design/ROUND4_SPEC.md section 5), built here only while
    parts/about.py has no render_page(): the CV and his profiles at the top,
    his biography beside the research areas his CV lists, then his career,
    and At a glance under it."""
    acts = "".join(f'<li><a href="{html.escape(h)}">{html.escape(t)}</a></li>'
                   for h, t in [("cv.html", "Download CV")]
                   + [(ln["href"], ln["label"]) for ln in links])
    areas_html = ""
    if areas:
        items = "".join(f"<li>{html.escape(a, quote=False)}</li>" for a in areas)
        areas_html = (f'<h2>Research areas</h2><ul>{items}</ul>'
                      f'<p><a href="research.html">My Research Areas</a></p>')
    rows = "".join(f"<li><time>{a}</time><div><h3>{b}</h3><p>{c}<br>{d}</p></div></li>"
                   for a, b, c, d in CAREER)
    return f"""<div class="wrap">
 <h1>About Me</h1>
 <div class="hero about">
  <div>
   <ul class="links">{acts}</ul>
   <h2>Biography</h2>
   {PROF_ABOUT}
  </div>
  <div class="about__aside">
   <img src="portrait.webp" srcset="portrait-280.webp 280w, portrait.webp 520w" sizes="230px"
        alt="Korkut Kaynardag" width="520" height="650">
   {areas_html}
  </div>
 </div>

 {timeline_html or f'<h2>Career timeline</h2><ul class="tl">{rows}</ul>'}
 {glance_html or ""}
</div>"""


def page_research(boxes_html=None, words=None):
    """My Research Areas: his text, the four boxes, and the educational
    sections (PROF_RESEARCH_MORE: the heading he extended, the paragraph he
    moved under it), in that order in the markup. parts/rboxes.py lays out
    .rboxes-page: on a narrow page the three run one after another; on a
    wide one the boxes stand in a column beside his text and the section."""
    words = words or {}
    boxes = "" if boxes_html else (
        box(SHORT, "image4.png",
            "Structural Health Monitoring / Non-destructive Testing <em>(Short)</em>",
            words.get(SHORT)) +
        box(EXTENDED, "image6.png",
            "Extended Structural Health Monitoring / Non-destructive Testing document",
            words.get(EXTENDED)) +
        box(SOUND, "image5.png", "Sound Wave Tracking", words.get(SOUND)) +
        '<div><div class="box"><b>Extensive ppt regarding my MSc and PhD Research</b>'
        '<img src="icon/image3.png" alt="" width="56" height="56"></div>'
        '<span class="dl off">Presentation, coming soon</span></div>')
    return f"""<div class="wrap">
 <h1>My Research Areas</h1>
 <div class="rboxes-page">
 <div class="rboxes-page__grid">
 <div class="col col--his">
  {PROF_RESEARCH}
 </div>

 {boxes_html or f'<div class="boxes">{boxes}</div>'}

 <div class="col rboxes-page__more">
  {PROF_RESEARCH_MORE}
 </div>
 </div>
 </div>
</div>"""


def row(href, name, note):
    """One row of a list of pages, as the fallbacks draw them (.rows)."""
    note = f"<em>{note}</em>" if note else ""
    return (f'<a class="row" href="{href}"><span><b>{name}</b>{note}</span>'
            f'<span class="row__go">{ARROW}</span></a>')


def page_title(href):
    """What a link to a page of the site is named: a document by its own
    title, another page by its row in the column."""
    path = href.split("#", 1)[0]
    if path.startswith("doc/"):
        return DOCS[path[4:-5]][0]
    return nav_title(path)


# The topics of his meeting note, in its order, each with the page that treats
# it, for the Big Picture's fallback while parts/documents.py has no
# render_big_picture() (the part keeps its own grouping). From Bridges to
# Photons follows Waves. Each opens its document whole: a reader reads a
# document from its start, so nothing links into a section of one
# (ROUND5_SPEC.md section 1; anchor_report() holds the site to it).
BIG_TOPICS = (
    ("Waves", f"doc/{WAVES}.html"),
    ("From Bridges to Photons", f"doc/{PHOTONS}.html"),
    ("Dynamics", f"doc/{WAVES}.html"),
    ("Signal Processing", f"doc/{SIGNAL}.html"),
    ("System Identification", f"doc/{SIGNAL}.html"),
    ("Estimation Theory", f"doc/{SIGNAL}.html"),
    ("Optimization", f"doc/{SIGNAL}.html"),
    ("Machine Learning", f"doc/{ML}.html"),
    ("Probability, Statistics", "probability-statistics.html"),
    ("Python / Programming", "python-programming.html"),
    ("Communication", "communication.html"),
)


def page_big_picture(part_html=None):
    if part_html:
        return wrap_page(BIG_PICTURE, part_html)
    topics = "".join(row(h, t, page_title(h) if h.startswith("doc/")
                         else "In preparation" if h in SOON else "")
                     for t, h in BIG_TOPICS)
    research = "".join(row(f"doc/{s}.html", DOCS[s][0], DOCS[s][1])
                       for s in (SHORT, EXTENDED, SOUND))
    return f"""<div class="wrap">
 <h1>{BIG_PICTURE}</h1>
 <div class="rows">{topics}</div>
 <h2>My Research Areas</h2>
 <div class="rows">{research}</div>
</div>"""


def soon_related(href):
    """The pages a topic in preparation links to, as parts/soon.py takes them."""
    return [{"href": h, "title": page_title(h)} for h in SOON[href]]


def page_soon(href, part_html=None):
    """A topic in preparation: his label and sub-line, and the pages already
    written that it draws on."""
    title = nav_title(href)
    if part_html:
        return wrap_page(title, part_html)
    sub = next(s for h, _, s, _ in NAV if h == href)
    sub = f"<p>{sub}</p>" if sub else ""
    rows = "".join(row(r["href"], r["title"], "") for r in soon_related(href))
    return f"""<div class="wrap">
 <h1>{title}</h1>
 <div class="col"><div class="pending"><span class="pending__tag">{SOON_STATE.get(href, "In preparation")}</span>
 {sub}</div></div>
 <h2>Related</h2>
 <div class="rows">{rows}</div>
</div>"""


def cv_text(value):
    """A CV entry as plain text, for the CV page's fallback."""
    if isinstance(value, dict):
        return ", ".join(cv_text(v) for v in value.values()
                         if isinstance(v, (str, int, list)) and v not in ("", []))
    if isinstance(value, list):
        return "; ".join(cv_text(v) for v in value)
    return html.escape(str(value), quote=False)


def page_cv(cv, part_html=None):
    """His CV (parts/cv.py), or while that part is missing a plain list of
    what content/cv/cv.json holds."""
    if part_html:
        return wrap_page("Curriculum Vitae", part_html)
    if not cv:
        return ('<div class="wrap">\n <h1>Curriculum Vitae</h1>\n <div class="col">'
                '<div class="pending"><span class="pending__tag">In preparation</span></div>'
                '</div>\n</div>')
    links = "".join(f'<li><a href="{html.escape(ln["href"])}">{html.escape(ln["label"])}</a></li>'
                    for ln in cv["links"])
    def section(s):
        entries = "".join(f"<li>{cv_text(e)}</li>" for e in s.get("entries", []))
        return (f'<h2 id="{html.escape(str(s.get("id", "")))}">'
                f'{html.escape(str(s.get("title", "")), quote=False)}</h2><ul>{entries}</ul>')

    body = "".join(section(s) for s in cv.get("sections", []))
    return f"""<div class="wrap">
 <h1>{html.escape(cv.get("name") or "Curriculum Vitae", quote=False)}</h1>
 <p>{html.escape(cv.get("location") or "", quote=False)}<br>
 <a href="mailto:{cv["email"]}">{cv["email"]}</a></p>
 <ul class="links">{links}</ul>
 <div class="col">{body}</div>
</div>"""


def page_contact(info, part_html=None):
    """Contact (parts/contact.py), or its plain fallback."""
    if part_html:
        return wrap_page("Contact", part_html)
    mail = info["email"]
    local, _, domain = mail.partition("@")
    links = "".join(f'<li><a href="{html.escape(ln["href"])}">{html.escape(ln["label"])}</a></li>'
                    for ln in info["links"])
    return f"""<div class="wrap">
 <h1>Contact</h1>
 <p class="lede">Feel free to reach out about research, collaboration, or the educational
 sections of this site, especially if you are a student or newcomer to these topics.</p>
 <ul class="find">
  <li><div><b>Email</b><a href="mailto:{mail}"
    aria-label="{mail}">{local}@<wbr>{domain}</a></div></li>
  <li><div><b>{info["department"]}</b>
    <em>{info["institute"]}, {info["city"]}, {info["country"]}</em></div></li>
 </ul>
 <ul class="links links--stack"><li><a href="{info["cv_href"]}">Curriculum vitae</a></li>
  {links}</ul>
</div>"""


def page_gallery(photos_html=None):
    """His photographs (parts/gallery.py), under the page's one heading."""
    return f"""<div class="wrap">
 <h1>Gallery</h1>
 {photos_html or '<div class="col"><p class="soon">Coming soon.</p></div>'}
</div>"""


def page_blog(list_html=None):
    return f"""<div class="wrap">
 <h1>Blog</h1>
 <p class="lede">The work that never made it into a paper: literature reviews, methods and
 experiments from my research, shared here in case they save you some of the time they took me.</p>
 {list_html or '<div class="col"><p class="soon">Coming soon.</p></div>'}
</div>"""


# ---------------------------------------------------------------- his CV

# his phone number, and any Gmail but his own public one (PUBLIC_EMAILS)
PRIVATE = re.compile(r"(?<!korkut\.kaynardag@)gmail|300\W{0,3}4065", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def load_cv(path=CV_JSON):
    """His CV as the site publishes it: content/cv/cv.json, or None while
    tools/cv_extract.py has not written it. The file must come clean: his
    personal Gmail or phone number, or any address but his institutional one,
    stops the build. It keeps only the profile links the site shows
    (LINK_KINDS; his CV's "Personal webpage" line is this site)."""
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    where = os.path.relpath(path, ROOT)
    if PRIVATE.search(raw):
        sys.exit(f"{where}: carries his personal Gmail or phone number, which the site must "
                 f"never publish; tools/cv_extract.py leaves both out")
    other = set(EMAIL.findall(raw)) - PUBLIC_EMAILS
    if other:
        sys.exit(f"{where}: an address the site must not carry: {sorted(other)}")
    cv = json.loads(raw)
    cv["email"] = CONTACT["email"]
    cv["links"] = [ln for ln in cv.get("links") or []
                   if ln.get("kind") in LINK_KINDS and ln.get("href") and ln.get("label")]
    cv["areas"] = list(cv.get("areas") or [])
    return cv


def profiles(cv):
    """The profile links About and Contact show: his CV's, of PROFILE_KINDS."""
    return [ln for ln in (cv or {}).get("links", []) if ln.get("kind") in PROFILE_KINDS]


def contact_info(cv):
    """What the Contact page shows, as parts/contact.py takes it."""
    return {"email": CONTACT["email"], "personal": CONTACT["personal"],
            "department": CONTACT["department"],
            "institute": CONTACT["institution"], "city": "Izmir", "country": "Turkiye",
            "links": profiles(cv), "cv_href": "cv.html"}


# ---------------------------------------------------------------- gallery and blog

# His old Wix gallery and blog, copied from the live site into content/ by
# tools/wix_pull.py: the originals Wix served, and a manifest for each.
GALLERY = os.path.join(ROOT, "content", "gallery")
BLOGSRC = os.path.join(ROOT, "content", "blog")
# Every picture the gallery and the blog publish is made once and kept here,
# by its source's hash and the settings: a rebuild copies instead of encoding.
CACHE = os.path.join(ROOT, "build", "webp")
PIPE = 1                     # raise when derive() changes what it writes

# Gallery sizes, by the long edge. A thumbnail serves a row photo up to about
# 400px wide at two device pixels to the CSS pixel; the full file is the
# viewer's, as large as a laptop screen shows a photo, never enlarged.
THUMB, THUMB_Q = 800, 72
FULL, FULL_Q = 2048, 80

# What Wix's static host accepts (dev.wix.com, "What You Can Upload"). A file
# of any other type is rejected at upload. A .docx is written only for a local
# preview, where the Word downloads work; --no-word, the build that goes to
# Wix, writes none, and --strict fails on anything else outside this list.
# .pdf joined on 27 Sep 2026 for the probability deck's download (round 11),
# released and then fetched from the live site to prove the host serves it.
WIX_TYPES = frozenset((".html", ".htm", ".css", ".js", ".mjs", ".cjs", ".jsx", ".map",
                       ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".avif",
                       ".bmp", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".json", ".xml",
                       ".txt", ".md", ".pdf"))
LOCAL_ONLY = frozenset((".docx",))


def file_types(paths, no_word=False):
    """(files for a local preview only, files Wix would reject) among `paths`."""
    local, bad = [], []
    for p in paths:
        ext = os.path.splitext(p)[1].lower()
        if ext in WIX_TYPES:
            continue
        (local if ext in LOCAL_ONLY and not no_word else bad).append(p)
    return local, bad


def derive(src, dst, edge=None, q=80, lossless=False, ground=(255, 255, 255)):
    """One published picture from a source file, through the cache. Returns
    its (width, height).

    The EXIF orientation is applied first, so a photo stands the way his phone
    held it; transparency is flattened onto `ground`; colour is converted to
    sRGB from any profile the file carries (his iPhone photos are Display P3,
    and a browser shown the raw values without the profile draws them dull);
    then the long edge is brought down to `edge`, never up. The WebP is
    written without EXIF, GPS, XMP or ICC: none of the camera's metadata, and
    none of the positions three of his photos still carry on Wix, is
    published."""
    import io
    from PIL import Image, ImageCms, ImageOps
    key = hashlib.sha256(f"{PIPE}|{sha256(src)}|{edge}|{q}|{lossless}|{ground}".encode()).hexdigest()
    hit = os.path.join(CACHE, key[:40] + ".webp")
    if not os.path.isfile(hit):
        with Image.open(src) as raw:
            icc = raw.info.get("icc_profile")
            im = ImageOps.exif_transpose(raw)
            if im.mode in ("RGBA", "LA", "P", "PA"):
                im = im.convert("RGBA")
                im = Image.alpha_composite(Image.new("RGBA", im.size, ground + (255,)), im)
            im = im.convert("RGB")
        if icc:
            try:
                im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)),
                                               ImageCms.createProfile("sRGB"), outputMode="RGB")
            except (ImageCms.PyCMSError, OSError, ValueError):
                print(f"  !! {os.path.basename(src)}: colour profile unreadable, kept as is")
        if edge and max(im.size) > edge:
            k = edge / max(im.size)
            im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))),
                           Image.LANCZOS)
        os.makedirs(CACHE, exist_ok=True)
        tmp = hit + ".part"
        if lossless:        # a page of text: exact, and smaller than lossy at readable quality
            im.save(tmp, "WEBP", lossless=True, quality=80, method=4)
        else:
            im.save(tmp, "WEBP", quality=q, method=6)
        os.replace(tmp, hit)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(hit, dst)
    from PIL import Image
    with Image.open(dst) as done:
        return done.size


def gallery_sets():
    """His gallery as the page shows it: each set once, in the live page's
    order. The live page showed its second set three times (the same three
    photos, first "at TTC", then twice "at TTCI"); the client decided to show
    it once, as it first appeared. manifest.json keeps all fourteen sets and
    marks the repeats (repeat_of)."""
    path = os.path.join(GALLERY, "manifest.json")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        m = json.load(fh)
    items = {i["order"]: i for i in m["items"]}
    return [{"lines": s["lines"], "items": [items[k] for k in s["items"]]}
            for s in m["sets"] if "repeat_of" not in s]


def make_gallery(out):
    """Write the gallery's files and return its sets as parts/gallery.py
    draws them: a thumbnail and a full file per photo, and for the film its
    poster at both sizes and the address its stream plays from."""
    ready = []
    for s in gallery_sets():
        its = []
        for it in s["items"]:
            n = f'{it["order"]:02d}'
            src = os.path.join(GALLERY, it["poster"]["file"] if it["type"] == "video" else it["file"])
            fw, fh = derive(src, os.path.join(out, "gallery", f"{n}.webp"), FULL, FULL_Q)
            tw, th = derive(src, os.path.join(out, "gallery", f"{n}-thumb.webp"), THUMB, THUMB_Q)
            rec = {"kind": it["type"], "full": f"gallery/{n}.webp", "fw": fw, "fh": fh,
                   "thumb": f"gallery/{n}-thumb.webp", "tw": tw, "th": th}
            if it["type"] == "video":
                # Wix's 720p copy: a 1080x1920 film shown at most about 900px
                # tall. It stays on his Wix media, fetched only on play.
                rec["stream"] = it["renditions"]["720p"]
                rec["duration"] = it.get("duration")
            its.append(rec)
        ready.append({"lines": s["lines"], "items": its})
    return ready


def blog_posts():
    """His posts, newest first, each its post.json (the Ricos body verbatim)."""
    path = os.path.join(BLOGSRC, "posts.json")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        index = json.load(fh)
    posts = []
    for p in index:
        with open(os.path.join(BLOGSRC, p["manifest"]), encoding="utf-8") as fh:
            posts.append(json.load(fh))
    return posts


def shown_date(iso):
    """2022-04-20 as he writes a date (About: "Since August 27, 2026")."""
    import datetime
    d = datetime.date.fromisoformat(iso[:10])
    return f"{d:%B} {d.day}, {d.year}"


def nodes_of(nodes):
    for n in nodes or []:
        yield n
        yield from nodes_of(n.get("nodes"))


def plain_text(node):
    return "".join(k["textData"]["text"] for k in nodes_of(node.get("nodes"))
                   if k.get("type") == "TEXT")


def tight(nodes):
    """The paragraphs Wix set with no space after them: each followed straight
    by another paragraph with words in it. His blank lines were empty
    paragraphs, and those keep the space (parts/blog.py, p-tight)."""
    out = set()
    for a, b in zip(nodes, nodes[1:]):
        if (a.get("type") == b.get("type") == "PARAGRAPH"
                and plain_text(a).strip() and plain_text(b).strip()):
            out.add(a.get("id"))
    return out


def lead(post):
    """His opening sentence, for the index: the first paragraph with words,
    up to its first full stop. His words, not an excerpt Wix cut mid-phrase."""
    for n in post["body"]["nodes"]:
        text = " ".join(plain_text(n).split())
        if n.get("type") == "PARAGRAPH" and text:
            m = re.match(r"(.+?[.!?:])(?=\s|$)", text)
            return html.escape(m.group(1) if m else text, quote=False)
    return ""


# His figures redrawn in the house style of the course notes (tools/blogfig/,
# 4 Oct 2026): content/blog-figs/<slug>/<stem>.svg stands in for the figure
# cut out of a screenshot of his text, text/<stem>.png, wherever it exists.
BLOGFIGS = os.path.join(ROOT, "content", "blog-figs")
SVG_PX = 1.6                 # px to the pt: a 10 pt label at 16 px, until the column scales it down


def redrawn(slug, name):
    """The redrawn figure for his cut-out picture `name` (data-crop) of post
    `slug`: (path, width, height), its size in px, or None if there is none."""
    path = os.path.join(BLOGFIGS, slug, os.path.splitext(name)[0] + ".svg")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        head = fh.read(600)
    # its size in pt is its viewBox (its width and height are 100%: alone it fills the window)
    m = re.search(r'<svg\b[^>]*?\sviewBox="0 0 ([\d.]+) ([\d.]+)"', head)
    if not m:
        sys.exit(f"{os.path.relpath(path, ROOT)}: no viewBox on its <svg>")
    return path, round(float(m.group(1)) * SVG_PX), round(float(m.group(2)) * SVG_PX)


def cut_out(slug, name, k, here):
    """Publish the figure `name` cut out of a screenshot of his text, the k-th
    picture of post `slug`, into the post's folder `here`: its redrawing, the
    SVG as it is, where there is one, else the cut-out picture as a lossless
    WebP. Returns (file name, width, height)."""
    stem = os.path.splitext(name)[0]
    fig = redrawn(slug, name)
    if fig:
        out_name = f"{k:02d}-{stem}.svg"
        os.makedirs(here, exist_ok=True)
        shutil.copyfile(fig[0], os.path.join(here, out_name))
        return out_name, fig[1], fig[2]
    out_name = f"{k:02d}-{stem}.webp"
    cw, ch = derive(os.path.join(BLOGSRC, slug, "text", name), os.path.join(here, out_name), lossless=True)
    return out_name, cw, ch


def shot(slug, k, here, name, rest, measure):
    """The figure for <img data-crop="name"...rest...> in a screenshot of his text,
    the k-th picture of post `slug`: published by cut_out(), its alt text first
    after its source, as preview.zoom() reads a picture. Drawn smaller than it
    is (as wide as the column or wider, and 480px or more: the rule of every
    picture of a post), it is marked fig--zoom, and zoom() links it to its own
    file, where a phone's reader can read its small type."""
    out_name, cw, ch = cut_out(slug, name, k, here)
    alt = re.search(r'\balt="([^"]*)"', rest)
    others = re.sub(r'\s*\balt="[^"]*"', "", rest).rstrip(" /")
    big = cw >= 480 and cw > measure * 0.9
    return (f'<figure class="shot{" fig--zoom" if big else ""}"><img src="{slug}/{out_name}" '
            f'alt="{alt.group(1) if alt else ""}" width="{cw}" height="{ch}" loading="lazy" '
            f'decoding="async"{others}>')


def blog_picture(post):
    """The post's first figure, for its card on the Blog: the first picture
    cut out of a screenshot of his text (text/<stem>.html, data-crop), which
    post_page() publishes as post/<slug>/<k>-<name>.webp at its own size, or
    as post/<slug>/<k>-<name>.svg where it is redrawn (redrawn()).
    His other pictures are pages of text and the film's poster is YouTube's,
    so a post without a cut-out figure has no picture. Returns {"src", "w",
    "h"}, the path from blog.html, or None."""
    from PIL import Image
    slug = post["slug"]
    for k, info in enumerate(post["images"], 1):
        page = os.path.join(BLOGSRC, slug, "text", os.path.splitext(info["file"])[0] + ".html")
        if not os.path.isfile(page):
            continue
        m = re.search(r'<img data-crop="([^"]+)"', open(page, encoding="utf-8").read())
        if m:
            stem = os.path.splitext(m.group(1))[0]
            fig = redrawn(slug, m.group(1))
            if fig:
                return {"src": f"post/{slug}/{k:02d}-{stem}.svg", "w": fig[1], "h": fig[2]}
            with Image.open(os.path.join(BLOGSRC, slug, "text", m.group(1))) as im:
                w, h = im.size
            return {"src": f"post/{slug}/{k:02d}-{stem}.webp", "w": w, "h": h}
    return None


# His library posts show screenshots of a folder of papers; the others show
# pages of a Word document. The alt line says which, and where in the post.
LIBRARY = frozenset(("literature-review-for-finite-element-model-updating",
                     "literature-review-for-the-comparison-of-multi-objective-optimization-algorithms"))


def picture_alt(slug, k, n):
    if slug in LIBRARY:
        return f"Part {k} of {n} of the screenshot of the library, shown as an image"
    return f"Page {k} of {n} of the post, shown as an image"


def post_page(post, out, no_word, newer=None, older=None, blog=None):
    """One post, post/<slug>.html: its pictures, poster and file written into
    post/<slug>/ and post/<slug>.docx, and its page. Returns (html, words):
    words are his paragraphs, which a --strict build finds on the page."""
    import copy
    import preview
    slug = post["slug"]
    nodes = copy.deepcopy(post["body"]["nodes"])
    here = os.path.join(out, "post", slug)
    figs, measure = {}, measure_px()
    pics = [n for n in nodes_of(nodes) if n.get("type") == "IMAGE"]
    for k, (node, info) in enumerate(zip(pics, post["images"], strict=True), 1):
        name = f"{k:02d}.webp"
        if os.path.isfile(os.path.join(BLOGSRC, slug, "text",
                                       os.path.splitext(info["file"])[0] + ".html")):
            figs[node["id"]] = {"src": f"{slug}/{name}", "w": 1, "h": 1, "zoom": False}
            continue  # set as text below; the screenshot does not ship
        w, h = derive(os.path.join(BLOGSRC, slug, info["file"]), os.path.join(here, name),
                      lossless=True)
        node["imageData"]["altText"] = picture_alt(slug, k, len(pics))
        figs[node["id"]] = {"src": f"{slug}/{name}", "w": w, "h": h,
                            "zoom": w >= 480 and w > measure * 0.9}
    for v in post.get("videos", []):
        meta = {"url": v["url"], "title": v.get("title"), "author": v.get("author")}
        if v.get("embed"):
            meta["embed"] = v["embed"]
        thumb = (v.get("thumbnail") or {}).get("file")
        if thumb and os.path.isfile(os.path.join(BLOGSRC, slug, thumb)):
            pw, ph = derive(os.path.join(BLOGSRC, slug, thumb), os.path.join(here, "video.webp"),
                            1280, 72)
            meta.update(poster=f"{slug}/video.webp", pw=pw, ph=ph)
        figs[v["node"]] = meta
    for f in post.get("files", []):
        if no_word:
            hosted = os.path.join(ROOT, "content", "word-urls.json")
            v = (json.load(open(hosted, encoding="utf-8")).get(f"post-{slug}")
                 if os.path.isfile(hosted) else None)
            figs[f["node"]] = ({"href": v["url"] + "?dn=" + urllib.parse.quote(v["name"]), "bytes": v["bytes"]} if v
                               else {"pending": True})
            continue
        src, dst = os.path.join(BLOGSRC, slug, f["file"]), os.path.join(out, "post", f"{slug}.docx")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        if sha256(src) != sha256(dst):
            sys.exit(f"post/{slug}.docx: the copy differs from its original")
        figs[f["node"]] = {"href": f"{slug}.docx", "bytes": os.path.getsize(dst)}
    # A screenshot of his text is set as text: content/blog/<slug>/text/<stem>.html
    # replaces the picture; a figure cut out of it is <img data-crop="x.png" alt="...">,
    # published as the cut-out picture, or as its redrawing where there is one.
    typed = {}
    for k, (node, info) in enumerate(zip(pics, post["images"]), 1):
        stem = os.path.splitext(info["file"])[0]
        src = os.path.join(BLOGSRC, slug, "text", stem + ".html")
        if os.path.isfile(src):
            text = open(src, encoding="utf-8").read()
            # <tex>TeX</tex> and <tex display>, set as his documents' formulas are
            import mathtex
            text = mathtex.typed(text, os.path.relpath(src, ROOT).replace(os.sep, "/"))

            text = re.sub(r'<img data-crop="([^"]+)"([^>]*)>',
                          lambda m, k=k: shot(slug, k, here, m.group(1), m.group(2), measure), text)
            typed[node["id"]] = f'<div class="typed">{text}</div>'
    close = tight(nodes)
    preview.plan(nodes, figs)
    try:
        parts = []
        for n in nodes:
            piece = preview.render(n, slug)
            ids = {x.get("id") for x in nodes_of([n])} & typed.keys()
            if ids:
                piece = "".join(typed[i] for i in ids)
            if n.get("id") in close:
                piece = re.sub(r'^<p(?: class="([^"]*)")?',
                               lambda m: f'<p class="{m.group(1) + " " if m.group(1) else ""}p-tight"',
                               piece, count=1)
            parts.append(piece)
        body = preview.zoom("".join(parts))
    finally:
        preview.plan([])
    VERBATIM.extend([body, html.escape(post["title"], quote=False)])
    words = [" ".join(plain_text(n).split()) for n in nodes if n.get("type") == "PARAGRAPH"]
    date = post["published"][:10]
    inner = blog.render_post(post["title"], date, shown_date(date), body, newer, older)
    page = shell(f"post/{slug}.html", html.escape(post["title"], quote=False) + " · Korkut Kaynardag",
                 inner, depth=1, foot=" foot--doc", section="blog.html",
                 desc=html.unescape(lead(post)) or post["title"])
    return page, [w for w in words if w]


def carries_metadata(path):
    """True when a picture file still holds camera metadata: an EXIF or XMP
    chunk in a WebP, an Exif or XMP segment in a JPEG, an eXIf chunk in a PNG.
    The containers are walked chunk by chunk, so bytes that merely spell EXIF
    inside the image data do not count."""
    import struct
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        i = 12
        while i + 8 <= len(data):
            tag, size = data[i:i + 4], struct.unpack("<I", data[i + 4:i + 8])[0]
            if tag in (b"EXIF", b"XMP "):
                return True
            i += 8 + size + (size & 1)
        return False
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 4 <= len(data) and data[i] == 0xFF:
            marker, size = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
            if marker == 0xDA:            # the image data starts: no more segments
                return False
            body = data[i + 4:i + 2 + size]
            if marker == 0xE1 and (body.startswith(b"Exif\x00") or b"ns.adobe.com/xap" in body[:64]):
                return True
            i += 2 + size
        return False
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        i = 8
        while i + 8 <= len(data):
            size, tag = struct.unpack(">I", data[i:i + 4])[0], data[i + 4:i + 8]
            if tag in (b"eXIf", b"iTXt") and (tag == b"eXIf" or b"XML:com.adobe.xmp" in data[i + 8:i + 40]):
                return True
            i += 12 + size
        return False
    return False


def metadata_report(out):
    """Every published picture that still carries camera metadata."""
    found = []
    for root, _, names in os.walk(out):
        for n in names:
            if os.path.splitext(n)[1].lower() in (".webp", ".jpg", ".jpeg", ".png"):
                path = os.path.join(root, n)
                if carries_metadata(path):
                    found.append(os.path.relpath(path, out).replace(os.sep, "/"))
    return found


# ---------------------------------------------------------------- the parts

PART_CSS = []
PART_JS = []
PART_SRC = []   # (file, css), for the em dash report


PART_ERRORS = []   # (part, error) for a part that exists but did not load


def part(name):
    """Import parts/<name>.py if it exists; return None while it is still being
    written. A part that exists but fails to load (a syntax error, a bad
    import) is also None, so the page falls back, but it is reported, and a
    --strict build fails on it."""
    try:
        mod = importlib.import_module(f"parts.{name}")
    except ModuleNotFoundError as e:
        if e.name != f"parts.{name}":
            PART_ERRORS.append((name, repr(e)))
            print(f"  !! parts/{name}.py did not load: {e!r}")
        return None
    except Exception as e:      # noqa: BLE001 - any failure is the part's, reported below
        PART_ERRORS.append((name, repr(e)))
        print(f"  !! parts/{name}.py did not load: {e!r}")
        return None
    css = getattr(mod, "CSS", "")
    PART_CSS.append(f"\n/* ===== {name} ===== */\n" + css)
    PART_SRC.append((f"parts/{name}.py", css))
    js = getattr(mod, "JS", "")
    if js.strip():
        PART_JS.append(f"\n/* ===== {name} ===== */\n(function(){{\n{js}\n}})();")
    return mod


def call(fn, **kw):
    """Call a part's render() with the keyword arguments its signature takes.

    A part that has not caught up with a new argument still builds, and says
    so: a stale signature must not silently drop the professor's own copy.
    """
    params = inspect.signature(fn).parameters
    if any(p.kind is p.VAR_KEYWORD for p in params.values()):
        return fn(**kw)
    dropped = [k for k in kw if k not in params]
    if dropped:
        print(f"  !! {fn.__module__}.{fn.__name__}() takes no {', '.join(dropped)}; "
              f"built without {'it' if len(dropped) == 1 else 'them'}")
    return fn(**{k: v for k, v in kw.items() if k in params})


# ---------------------------------------------------------------- the checks

def _ctx(text, m):
    s = re.sub(r"<[^>]*>|^[^<]*>|<[^>]*$", "", text[max(0, m.start() - 70):m.end() + 70])
    return re.sub(r"\s+", " ", s).strip()


def emdash_report(out):
    """Every em dash on the built site, billed to the file that wrote it.

    Our own text takes none: a colon, a comma, a full stop, or a closed-up en
    dash in a range. His sentences (the PROF_ blocks) and his converted Word
    documents ship as he wrote them and are exempt. A spaced en dash is listed
    too, since in running text it is a dash, not a range.
    Returns [(owner, where, context, kind)].
    """
    hits = []
    kinds = (("em dash", DASH), ("spaced en dash", SPACED_EN))
    verbatim = sorted(set(VERBATIM), key=len, reverse=True)   # a whole body before a heading

    def bare_html(markup):
        return re.sub(r"<(script|style)\b.*?</\1>", "", markup, flags=re.S | re.I)

    # A part's markup can hold another part's: the hero holds the illustration,
    # About holds the career. Each dash is billed to the innermost part that
    # wrote it, and the page is cleared of every part before build.py's share.
    owned = []
    for owner, frag in OWNED:
        frag = bare_html(frag)
        if frag and (owner, frag) not in owned:
            owned.append((owner, frag))
    longest = sorted(owned, key=lambda of: len(of[1]), reverse=True)
    for root, _, names in os.walk(out):
        for name in sorted(names):
            if not name.endswith(".html"):
                continue
            where = os.path.relpath(os.path.join(root, name), out).replace(os.sep, "/")
            with open(os.path.join(root, name), encoding="utf-8") as fh:
                text = bare_html(fh.read())
            for owner, frag in owned:
                if frag not in text:
                    continue
                own = frag
                for _, inner in longest:
                    if len(inner) < len(frag) and inner in own:
                        own = own.replace(inner, "")
                for v in verbatim:
                    own = own.replace(v, "")
                hits += [(owner, where, _ctx(own, m), k) for k, p in kinds for m in p.finditer(own)]
            for _, frag in longest:
                text = text.replace(frag, "")
            for v in verbatim:
                text = text.replace(v, "")
            hits += [("build.py", where, _ctx(text, m), k) for k, p in kinds for m in p.finditer(text)]
    # a stylesheet can print a dash too, through `content`
    for owner, css in [("build.py", CSS)] + PART_SRC:
        for m in re.finditer(r"content\s*:[^;}]*", css):
            if re.search(r"\\0*2014|\u2014", m.group()):
                hits.append((owner, "stylesheet", m.group().strip(), "em dash"))
    return hits


def link_report(out):
    """Every local href, src and url() on the built site that does not resolve.

    The file must exist with exactly that case (Wix serves case-sensitively,
    Windows does not) inside the site, and a #fragment must name an id there.
    """
    problems, ids = [], {}

    def exact(path):
        rel = os.path.relpath(path, out)
        if rel.startswith(".."):
            return False
        cur = out
        for seg in rel.split(os.sep):
            if seg not in os.listdir(cur):
                return False
            cur = os.path.join(cur, seg)
        return os.path.isfile(cur)

    def page_ids(path):
        if path not in ids:
            with open(path, encoding="utf-8") as fh:
                ids[path] = set(re.findall(r'\bid="([^"]+)"', fh.read()))
        return ids[path]

    for root, _, names in os.walk(out):
        for name in names:
            if not name.endswith((".html", ".css")):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            if name.endswith(".html"):
                refs = re.findall(r'\b(?:href|src)="([^"]*)"', text)
                refs += [c.split()[0] for s in re.findall(r'\bsrcset="([^"]*)"', text)
                         for c in s.split(",") if c.strip()]
            else:
                refs = re.findall(r"url\(\s*[\"']?([^\"')]+)", text)
            where = os.path.relpath(path, out).replace(os.sep, "/")
            for ref in refs:
                url = html.unescape(ref).strip()
                if not url or re.match(r"(?:[a-z][a-z0-9+.-]*:|//)", url, re.I):
                    continue          # another site, or mailto:
                u = urlsplit(url)
                target = os.path.normpath(os.path.join(root, unquote(u.path))) if u.path else path
                if not exact(target):
                    problems.append(f"{where}: {url} -> no such file")
                elif u.fragment and target.endswith(".html") and u.fragment not in page_ids(target):
                    problems.append(f"{where}: {url} -> no id \"{u.fragment}\"")
    return problems


# A string in a script that names a place in a document: "doc/<slug>.html#x".
_DOC_PLACE = re.compile(r"""["'`]([^"'`\s]*\bdoc/[^"'`\s#/]+\.html#[^"'`\s]*)""")


def anchor_report(out):
    """Every link to a place inside a document (doc/<slug>.html#...) from
    anywhere but that document's own page. His documents are read whole, from
    their start (ROUND5_SPEC.md section 1): a document's own Contents and its
    in-page links may go to a section of it, nothing else on the site may,
    the column, the Big Picture and the other documents included. The pages'
    links are resolved from the page, so a document linking another's section
    by its bare file name is caught too; a script's strings are read as well,
    for a link it would write at run time.
    Returns [(file, link)]."""
    found = []
    for root, _, names in os.walk(out):
        for name in sorted(names):
            if not name.endswith((".html", ".js")):
                continue
            path = os.path.normpath(os.path.join(root, name))
            where = os.path.relpath(path, out).replace(os.sep, "/")
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            if name.endswith(".html"):
                refs, base = re.findall(r'\bhref="([^"]*#[^"]*)"', text), root
            else:
                refs, base = _DOC_PLACE.findall(text), out
            for ref in refs:
                url = html.unescape(ref).strip()
                if re.match(r"(?:[a-z][a-z0-9+.-]*:|//)", url, re.I):
                    continue          # another site
                u = urlsplit(url)
                if not u.path or not u.fragment:
                    continue          # a place on the same page, or no place
                target = os.path.normpath(os.path.join(base, unquote(u.path)))
                rel = os.path.relpath(target, out).replace(os.sep, "/")
                if rel.startswith("doc/") and rel.endswith(".html") and target != path:
                    found.append((where, url))
    return found


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# His deck: the four-slide mockup of 24 September 2026 (slide 1 the home page,
# 2 About Me, 3 My Research Areas, 4 the band alone); the one before it is
# kept beside it as "NEW WAVES AND DATA (2026-09-21).pptx". The slide each of
# his blocks was transcribed from, and the slide with the column he drew:
DECK = os.path.join(SRC, "NEW WAVES AND DATA.pptx")
DECK_SLIDE = {"PROF_HEADER": 1, "PROF_BIO": 1, "PROF_MOTIVATION": 1,
              "PROF_ABOUT": 2, "PROF_RESEARCH": 3, "PROF_RESEARCH_MORE": 3}
NAV_SLIDE = 1
# his deck types a power with the Unicode superscript digits
SUPERSCRIPT = str.maketrans("0123456789", "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077"
                                          "\u2078\u2079")


def _words(text):
    """Text as a reader gets it: tags gone, entities decoded, whitespace collapsed."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", text)).split())


# the list marks he typed in front of a paragraph: "1) ", "- "
LIST_MARK = re.compile(r"^(?:\d+\)|[-\u2013\u2022])\s+")


def _paragraphs(numbers):
    """Each slide in `numbers` as its list of paragraphs, as _words reads
    them, with the list mark he typed in front of one ("1) ", "- ") taken
    off: the site draws those marks itself."""
    import zipfile
    out = {}
    with zipfile.ZipFile(DECK) as z:
        for k in sorted(set(numbers)):
            xml = z.read(f"ppt/slides/slide{k}.xml").decode("utf-8")
            paras = (_words("".join(re.findall(r"<a:t>(.*?)</a:t>", p, re.S)))
                     for p in re.findall(r"<a:p>(.*?)</a:p>", xml, re.S))
            out[k] = [LIST_MARK.sub("", p) for p in paras if p]
    return out


def _slides(numbers):
    """The text of each slide in `numbers`, paragraph by paragraph, as _words reads it."""
    import zipfile
    out = {}
    with zipfile.ZipFile(DECK) as z:
        for k in sorted(set(numbers)):
            xml = z.read(f"ppt/slides/slide{k}.xml").decode("utf-8")
            paras = re.findall(r"<a:p>(.*?)</a:p>", xml, re.S)
            out[k] = _words(" ".join(
                "".join(re.findall(r"<a:t>(.*?)</a:t>", p, re.S)) for p in paras))
    return out


# Changes to his text that were approved, each as our text, the words of his
# deck it stands for, and the reason. The deck is compared with the words he
# wrote, so each is put back first, whatever the line breaks; and each must
# still stand in its block, or the block went back to words since changed
# (deck_report()). His editorial markup of 27 Sep 2026 is newer than the deck
# (every mark read in tools/ROUND11_EDITS.md): each change it made is one of
# these, a heading he extended or a point he typed standing, whole, for what
# the deck has in its place.
WHY_MOVED = ("the user's approval, 2026-09-25: the documents moved from Gallery to the Big "
             "Picture page")
WHY_MARKUP = "professor's editorial markup, 27 Sep 2026 (reference/prof-edits/)"
APPROVED_EDITS = {
    "PROF_MOTIVATION": [
        ("identification, probability, statistics, estimation, stochastic process, machine "
         "learning, Python and programming after", "identification, and machine learning after",
         WHY_MARKUP),
        # his typed note is the first point; the old first point follows the
        # second, after the "and" he wrote under it
        ("<li>What methods are in each topic, what they actually do (the intuition and logic), "
         "and thus what the big picture of each topic is</li> <li>What kinds of problems they "
         "solve and where these methods are applied</li>",
         "<li>Where these methods are applied</li> <li>What kinds of problems they solve</li>",
         WHY_MARKUP),
        # what he typed after "journey.", bold at his note, and "aim" for "want"
        ("journey. <strong>These sections are designed not to teach your mathematics of each "
         "method/algorithm, but rather than make you figure out the answers of the 4 questions "
         "above. Accordingly,</strong> I aim to help", "journey. I want to help", WHY_MARKUP),
        ("in your work.", "in your work", WHY_MARKUP)],
    "PROF_RESEARCH": [
        ("took me to industry", "took me through industry", WHY_MARKUP),
        ("as an applied data scientist and a Senior AI Engineer", "as a Senior AI Engineer",
         WHY_MARKUP),
        ("documents on the right introduce my research topics",
         "documents below introduce these topics", WHY_MARKUP)],
    "PROF_RESEARCH_MORE": [
        # the heading is ours, with the words in brackets he added; his deck has none
        ("<h2>The educational sections (topics in the big picture menu)</h2>", "", WHY_MARKUP),
        ("You'll also find documents about the topics that I used extensively",
         "You'll find these documents under the three sections", WHY_MARKUP),
        ('<a class="inlink" href="big-picture.html">Big Picture</a>', "Gallery", WHY_MOVED)],
}
# The paragraphs his editorial markup of 27 Sep 2026 struck ("Delete, Delete"),
# by the words each opens with: the section under his research text, before
# his second paragraph moved there. deck_report() takes them out of his slide,
# so no block may carry them again.
STRUCK = {3: ("Also, are you also asking", "In this webpage, I also explain")}


def deck_rows(source):
    """A deck's slides in order and whether a manifest listed them: its
    content/<source>/deck.json (tools/deck/render.py: label, stem, title and,
    for a slide that plays, anim), or, for a deck without one, every
    sNNN-1600.webp in its web/ folder numbered 1 to n, untitled."""
    path = os.path.join(ROOT, "content", source, "deck.json")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh), True
    web_src = os.path.join(ROOT, "content", source, "web")
    n = sum(1 for f in (os.listdir(web_src) if os.path.isdir(web_src) else ())
            if re.fullmatch(r"s\d{3}-1600\.webp", f))
    return [{"label": str(k), "stem": f"s{k:03d}", "title": None} for k in range(1, n + 1)], False


def deck_report():
    """Each paragraph, list item and heading of every PROF_ block, set against
    the paragraphs of the slide it came from: each must be one of them, whole,
    once the list mark he typed ("1) ", "- ") is off. The on-page check below
    only proves a block reached its page unchanged; this one proves the block
    is his. Whole paragraphs, not a search of the slide's text: a passage that
    lost its last character, his colon after "Topics that I use in my
    research", is still found inside the slide, but it is no longer his
    paragraph, and a comma, a full stop, a quotation mark or a capital that
    differs anywhere in a passage fails it the same way. And each passage
    must be its own paragraph: a block is a run of his paragraphs, in his
    order, so "Myself:" that lost its colon is not let through because his
    intro list also has a "Myself" (_align()). A power, MathML's <msup> of
    digits or a <sup> of digits, is read as the superscript digits his deck
    types, so the band's <msup><mn>10</mn><mn>27</mn></msup> is checked as
    "10²⁷".
    His approved changes (APPROVED_EDITS) are put back first, and each must
    be in its block: a block that reads as his deck but lacks one (the full
    stop he added, say) went back to words he has since changed. The
    paragraphs his markup struck (STRUCK) are no longer his slide's.
    Returns (passages checked, [(block, passage that is not one of his
    paragraphs, or approved change it lost)]); a struck paragraph that is not
    exactly one of his slide's is reported as ("STRUCK", its opening words)."""
    paras = _paragraphs(DECK_SLIDE.values())
    checked, missing = 0, []
    for k, gone in STRUCK.items():
        missing += [("STRUCK", w) for w in gone if sum(p.startswith(w) for p in paras[k]) != 1]
        paras[k] = [p for p in paras[k] if not p.startswith(gone)]
    for name, k in DECK_SLIDE.items():
        block = re.sub(r"<msup>\s*<mn>(\d+)</mn>\s*<mn>(\d+)</mn>\s*</msup>",
                       lambda m: m.group(1) + m.group(2).translate(SUPERSCRIPT),
                       globals()[name])
        block = re.sub(r"<sup>(\d+)</sup>", lambda m: m.group(1).translate(SUPERSCRIPT),
                       block)
        block, lost = " ".join(block.split()), []
        for ours, his, _why in APPROVED_EDITS.get(name, ()):
            ours = " ".join(ours.split())
            if ours not in block:
                lost.append(_words(ours))
            block = block.replace(ours, his)
        passages = [p for p in (_words(x) for x in
                                re.split(r"</?(?:p|li|ul|ol|h2|div)\b[^>]*>", block)) if p]
        checked += len(passages)
        at = _align(passages, paras[k])
        astray = [(name, p) for i, p in enumerate(passages)
                  if at + i >= len(paras[k]) or paras[k][at + i] != p]
        missing += astray or [(name, w) for w in lost]
    return checked, missing


def _align(passages, paras):
    """Where a block's passages stand among its slide's paragraphs: the start
    of the run of paragraphs that equals the most of them, in order, and of
    runs as good as each other, the one whose other paragraphs come nearest
    to the passages that differ (so a passage one character short is set
    against its own paragraph, and that is the one reported)."""
    import difflib
    n = len(passages)
    starts = range(max(1, len(paras) - n + 1))

    def same(s):
        return sum(1 for i, p in enumerate(passages) if s + i < len(paras) and paras[s + i] == p)

    best = max(same(s) for s in starts)
    ties = [s for s in starts if same(s) == best]
    return max(ties, key=lambda s: sum(
        difflib.SequenceMatcher(None, p, paras[s + i]).quick_ratio()
        for i, p in enumerate(passages) if s + i < len(paras)))


def _tokens(text):
    return " " + " ".join(re.findall(r"[a-z0-9]+", text.lower())) + " "


def nav_report():
    """Each title and sub-line of the column, set against the column he drew
    on slide 1: his words in his order, the separators and capitals aside,
    since a title drops the comma that runs it on into its sub-line and his
    "presentations. Reports. papers" takes commas. The rows the client named
    (NAV_OURS) are left out.
    Returns (labels checked, [labels his slide does not have])."""
    slide = _tokens(_slides([NAV_SLIDE])[NAV_SLIDE])
    labels = [label for href, title, sub, _ in NAV if href not in NAV_OURS
              for label in (title, sub) if label]
    return len(labels), [label for label in labels if _tokens(label) not in slide]


# The files a browser reads as text, which private_report() searches.
TEXT_TYPES = frozenset((".html", ".htm", ".css", ".js", ".mjs", ".cjs", ".json", ".xml",
                        ".svg", ".txt", ".md", ".map"))


def private_report(out):
    """What the site must never publish, wherever it turns up: his personal
    Gmail or phone number (both are in his Word CV), any email address but his
    institutional one, and the Word CV itself under any name. Text files are
    read as they are; a Word file is opened and its XML read.
    Returns [(file, what was found)]."""
    import zipfile
    found = []
    cv = (os.path.getsize(CV_DOCX), sha256(CV_DOCX)) if os.path.isfile(CV_DOCX) else None
    for root, _, names in os.walk(out):
        for name in sorted(names):
            path = os.path.join(root, name)
            where = os.path.relpath(path, out).replace(os.sep, "/")
            ext = os.path.splitext(name)[1].lower()
            if "resume" in name.lower() or (cv and os.path.getsize(path) == cv[0]
                                            and sha256(path) == cv[1]):
                found.append((where, "his Word CV"))
            texts = []
            if ext in TEXT_TYPES:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    texts.append(fh.read())
            elif ext == ".docx":
                try:
                    with zipfile.ZipFile(path) as z:
                        texts += [z.read(n).decode("utf-8", "replace") for n in z.namelist()
                                  if n.endswith((".xml", ".rels"))]
                except zipfile.BadZipFile:
                    found.append((where, "a Word file that cannot be opened to check"))
            for text in texts:
                found += [(where, m.group()) for m in PRIVATE.finditer(text)]
                found += [(where, a) for a in sorted(set(EMAIL.findall(text)) - PUBLIC_EMAILS)]
    return found


def bare(text):
    """A stylesheet or script as it ships: without its /* */ comments, which are
    notes to us, and without the blank lines they leave. Other whitespace
    stays, since calc() needs its spaces."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return "\n".join(ln.rstrip() for ln in text.split("\n") if ln.strip()) + "\n"


def page_rgb():
    """--page from parts/theme.py as an RGB triple: the paper that a picture
    drawn on a transparent ground is flattened onto."""
    try:
        from parts import theme
        m = re.search(r"--page:\s*#([0-9A-Fa-f]{6})", theme.CSS)
    except ImportError:
        m = None
    return tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4)) if m else (255, 255, 255)


# ---------------------------------------------------------------- the build

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Build the wavesanddata static site.")
    ap.add_argument("--out", help="output directory (default: site/dist). Give each concurrent "
                                  "builder its own, because the build deletes it first.")
    ap.add_argument("--strict", action="store_true",
                    help="also fail on an em dash a part wrote, and on a broken link")
    ap.add_argument("--no-word", action="store_true",
                    help="publish no .docx files and show the Word links as pending. Wix's "
                         "instant static host serves only HTML, CSS, JS, images and fonts; "
                         "a .docx uploaded there is dropped and its link would 404.")
    args = ap.parse_args()
    global OUT
    if args.out:
        OUT = os.path.abspath(args.out)

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "doc"))

    from PIL import Image

    paper = page_rgb()

    def flat(src, ground=None):
        """The picture on an opaque ground (the paper by default), or with its
        own transparency kept where `ground` is False."""
        im = Image.open(src)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            if ground is False:
                return im if im.getchannel("A").getextrema()[0] < 255 else im.convert("RGB")
            bg = Image.new("RGBA", im.size, (ground or paper) + (255,))
            return Image.alpha_composite(bg, im).convert("RGB")
        return im.convert("RGB")

    def web(im, dst, maxw, q=80):
        if im.width > maxw:
            im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
        im.save(dst, "WEBP", quality=q, method=6)
        return im.size

    # The portrait, pre-cropped to 4:5 (DESIGN_BRIEF.md section 6): the 700px-wide
    # resize is 700x683, and the crop keeps its full height and trims the width.
    # Checked by eye on the result: the face sits within 4px of the centre (hair
    # x 219-465 at y 150, glasses 247-453 at y 240), the eye line 37% down.
    im = flat(os.path.join(ICONS, "headshot-708.png"))
    im = im.resize((700, round(im.height * 700 / im.width)), Image.LANCZOS)
    crop = im.crop((90, 0, 610, 650))
    crop.save(os.path.join(OUT, "portrait.webp"), "WEBP", quality=80, method=6)
    # and a 280px copy for 1x screens: the hero draws the portrait at 280px and
    # About at 230, so only a denser screen needs the 520px file (srcset)
    crop.resize((280, 350), Image.LANCZOS).save(
        os.path.join(OUT, "portrait-280.webp"), "WEBP", quality=80, method=6)
    # His portrait at the head of the column and in the phone's bar
    # (portrait()): the square PORTRAIT_BOX from the headshot at its full 708px,
    # brought down in one step to each width a screen asks for, so the 2x file
    # is as sharp as the 1x. A face this small carries its detail in the
    # glasses and the eyes, so it is written at quality 85, not 80: 3 to 9 KB.
    square = flat(os.path.join(ICONS, "headshot-708.png")).crop(PORTRAIT_BOX)
    for w in PORTRAIT_SQ:
        square.resize((w, w), Image.LANCZOS).save(
            os.path.join(OUT, f"portrait-sq-{w}.webp"), "WEBP", quality=85, method=6)

    # The fonts and the license they ship under (FONT_DIR), byte for byte.
    os.makedirs(os.path.join(OUT, "fonts"))
    for n in sorted(os.listdir(FONT_DIR)):
        shutil.copyfile(os.path.join(FONT_DIR, n), os.path.join(OUT, "fonts", n))

    # The audited Word originals, copied byte for byte to doc/<slug>.docx and
    # proved identical to his files in content/source/.
    words = {}
    for slug in () if args.no_word else HOSTED_DOCX:
        name, file = SRC_DOCX[slug], f"{slug}.docx"
        src, dst = os.path.join(SRC, name), os.path.join(OUT, "doc", file)
        shutil.copyfile(src, dst)
        if sha256(src) != sha256(dst):
            sys.exit(f"doc/{file}: the copy differs from content/source/{name}")
        words[slug] = (file, os.path.getsize(dst), name)
    print(f"Word: {len(words)} files in doc/, each SHA-256 identical to its original")
    # With --no-word the site links the sanitized copies in the Media Manager
    # of the site on wavesanddata.com (tools/wix_word.py wrote their addresses).
    hosted = os.path.join(ROOT, "content", "word-urls.json")
    if args.no_word and os.path.isfile(hosted):
        for slug, v in json.load(open(hosted, encoding="utf-8")).items():
            if slug in DOCS:
                words[slug] = (v["url"] + "?dn=" + urllib.parse.quote(v["name"]), v["bytes"], v["name"])
        print(f"Word: {len(words)} files linked from the Media Manager")

    with open(os.path.join(OUT, "style.css"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(bare(CSS))

    # Order matters: theme defines the tokens, shell overrides the base stylesheet.
    theme = part("theme")
    global BPNAV
    BPNAV = part("bpnav")
    if not theme:
        sys.exit("parts/theme.py did not load, and without it the site has no tokens")
    # the home page: the band across the top, the illustration and the hero
    # that holds it, the topic cards
    masthead, heroart = part("masthead"), part("heroart")
    hero, topics = part("hero"), part("topics")
    # His motivation block. parts/motivation.py, when present, restages it; it is
    # handed his own HTML so his words still come from PROF_MOTIVATION alone.
    motivation = part("motivation")
    rboxes = part("rboxes")
    # The career timeline is its own module. WAD_TIMELINE lets a designer build the
    # page with a candidate (e.g. timeline_a) without touching this file.
    tl_name = os.environ.get("WAD_TIMELINE", "timeline")
    timeline = part(tl_name)
    about = part("about")
    docs_css = part("docs")
    # after docs: a post page is a document page, and blog.py adds to it
    dlist, gal, blog = part("documents"), part("gallery"), part("blog")
    cvpart, contact, soon = part("cv"), part("contact"), part("soon")
    deckpart = part("deck")
    shell_css = part("shell")
    loaded = [n for n, m in (("theme", theme), ("masthead", masthead), ("heroart", heroart),
                             ("hero", hero), ("topics", topics), ("motivation", motivation),
                             ("rboxes", rboxes), (tl_name, timeline), ("about", about),
                             ("docs", docs_css), ("documents", dlist), ("gallery", gal),
                             ("blog", blog), ("cv", cvpart), ("contact", contact),
                             ("soon", soon), ("deck", deckpart), ("bpnav", BPNAV),
                             ("shell", shell_css)) if m]
    print("parts:", ", ".join(loaded))

    with open(os.path.join(OUT, "parts.css"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(bare("".join(PART_CSS)))
    PART_JS.insert(0, f"\n/* ===== shell (build.py) ===== */\n(function(){{\n{JS}\n}})();")
    with open(os.path.join(OUT, "parts.js"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(bare("".join(PART_JS)))

    if not rboxes:        # the fallback boxes draw the deck's own icons
        os.makedirs(os.path.join(OUT, "icon"))
        for n in ("image3.png", "image4.png", "image5.png", "image6.png"):
            shutil.copy(os.path.join(ICONS, n), os.path.join(OUT, "icon", n))

    # his photographs and his posts, from content/ (tools/wix_pull.py)
    sets = make_gallery(OUT) if gal else []
    posts = blog_posts()
    n_photos = sum(1 for st in sets for it in st["items"] if it["kind"] == "photo")
    print(f"gallery: {len(sets)} sets, {n_photos} photos and "
          f"{sum(len(st['items']) for st in sets) - n_photos} film, each a thumbnail up to "
          f"{THUMB}px and a full file up to {FULL}px; blog: {len(posts)} posts")
    # his CV, from content/cv/cv.json (tools/cv_extract.py); a file that is not
    # clean stops the build in load_cv()
    cv = load_cv()
    print("cv: " + (f"content/cv/cv.json, {len(cv.get('sections') or [])} sections, "
                    f"{len(cv['links'])} profile links, {len(cv['areas'])} research areas"
                    if cv else "no content/cv/cv.json yet, the CV page waits"))
    links, areas = profiles(cv), (cv or {}).get("areas", [])
    if cv and cvpart and hasattr(cvpart, "his"):
        # his CV's words are his: a dash inside one is not billed to parts/cv.py
        VERBATIM.extend(t for t in cvpart.his(cv) if DASH.search(t) or SPACED_EN.search(t))

    # Each part through the interface design/ROUND4_SPEC.md section 10 gives
    # it. ready() is None while a part is missing or does not take those
    # arguments yet, and the page then comes from the fallback here.
    mast_html = (mine("parts/masthead.py", ready(masthead, "render", PROF_HEADER))
                 or MAST_FALLBACK)
    art_html = mine("parts/heroart.py", ready(heroart, "render"))
    hero_html = mine("parts/hero.py", hero and call(hero.render, contact=CONTACT,
                                                    intro=PROF_INTRO, bio=PROF_BIO,
                                                    art=art_html))
    topics_html = mine("parts/topics.py", ready(topics, "render", items=topic_items()))
    if timeline:
        timeline_html = mine(f"parts/{tl_name}.py", timeline.render())
    else:
        timeline_html = mine("parts/about.py", ready(about, "render_timeline"))
    about_html = mine("parts/about.py", ready(about, "render_page", PROF_ABOUT, links, areas,
                                              timeline_html))
    pages = {
        "index.html": ("Korkut Kaynardag, PhD", page_home(
            hero_html, topics_html,
            mine("parts/motivation.py", motivation and motivation.render(PROF_MOTIVATION)))),
        "about.html": ("About Me · Korkut Kaynardag",
                       wrap_page("About Me", about_html) if about_html else page_about(
                           timeline_html, links, areas,
                           mine("parts/about.py", ready(about, "render_glance")))),
        "cv.html": ("Curriculum Vitae · Korkut Kaynardag", page_cv(
            cv, cv and mine("parts/cv.py", ready(cvpart, "render", cv)))),
        "research.html": ("My Research Areas · Korkut Kaynardag", page_research(
            mine("parts/rboxes.py", rboxes and call(
                rboxes.render, docs_ready=bool(words),
                sizes={s: w[1] for s, w in words.items()},
                hrefs={s: w[0] if w[0].startswith("http") else f"doc/{w[0]}" for s, w in words.items()})), words)),
        "gallery.html": ("Gallery · Korkut Kaynardag", page_gallery(
            mine("parts/gallery.py", gal and sets and gal.render(sets)))),
        "blog.html":("Blog · Korkut Kaynardag", page_blog(
            mine("parts/blog.py", blog and posts and blog.render_index(
                [{"href": f"post/{p['slug']}.html", "title": p["title"],
                  "date": p["published"][:10], "shown": shown_date(p["published"]),
                  "lead": lead(p), "pic": blog_picture(p)} for p in posts])))),
        "contact.html": ("Contact · Korkut Kaynardag", page_contact(
            contact_info(cv), mine("parts/contact.py", ready(contact, "render",
                                                             contact_info(cv))))),
    }
    for href in SOON:
        pages[href] = (f"{nav_title(href)} · Korkut Kaynardag", page_soon(href, mine(
            "parts/soon.py", ready(soon, "render", nav_title(href),
                                   next(s for h, _, s, _ in NAV if h == href),
                                   soon_related(href)))))
    cmu = os.path.join(ROOT, "content", "fonts-cmu")
    if os.path.isdir(cmu):  # Computer Modern for the CV's printed PDF (OFL)
        os.makedirs(os.path.join(OUT, "fonts"), exist_ok=True)
        for f in os.listdir(cmu):
            if f.endswith(".woff2"):
                shutil.copyfile(os.path.join(cmu, f), os.path.join(OUT, "fonts", f))
    # His decks, a slide viewer each (parts/deck.py). Every slide is in its
    # deck's web/ folder three times, <stem>-320, -960 and -1600.webp, and goes
    # to deck/<folder>/. A deck with an SVG for every slide publishes no 1600
    # copy: its vectors draw every size the 960 copy cannot (28 Sep 2026, to
    # keep the site well under Wix's 100 MB; the copies stay in content/). A
    # deck with a manifest (deck.json, tools/deck/render.py) goes by it: its
    # slides in order, each with its label (65a for a slide of ours after his
    # 65), stem and title, his words, so a dash in one is his (VERBATIM). A
    # slide that plays brings its page, anim/<stem>.html, and the files those
    # pages share; their fonts are the site's fonts/, and the deck's Latin
    # Modern Math subset joins them there. While the part is missing, the
    # slides are listed one under the other.
    slides = {}     # deck page -> the slides this build wrote, for the Big Picture
    for href, source, folder, head, h1 in (
            ("presentation.html", "deck-phd", "phd", "MSc and PhD Research Presentation",
             "Extensive ppt regarding my MSc and PhD Research"),
            ("probability-statistics.html", "deck-probstat", "probability",
             "Probability, statistics and estimation", "Probability, statistics and estimation")):
        web_src = os.path.join(ROOT, "content", source, "web")
        rows, manifest = deck_rows(source)
        count = len(rows)
        if not count:
            continue
        slides[href] = count
        # a page description that names the slides names them rightly
        said = re.search(r"in (\d+) slides", PAGE_DESC.get(href, ""))
        if said and int(said.group(1)) != count:
            sys.exit(f"{href}: PAGE_DESC says {said.group(1)} slides, the deck has {count}")
        os.makedirs(os.path.join(OUT, "deck", folder), exist_ok=True)
        svgs = [f"{r['stem']}.svg" for r in rows]
        vector = all(os.path.isfile(os.path.join(web_src, f)) for f in svgs)
        for r in rows:
            for w in (320, 960) if vector else (320, 960, 1600):
                f = f"{r['stem']}-{w}.webp"
                shutil.copyfile(os.path.join(web_src, f), os.path.join(OUT, "deck", folder, f))
        titles = [r["title"] for r in rows] if any(r["title"] for r in rows) else None
        VERBATIM.extend(t for t in titles or () if t and (DASH.search(t) or SPACED_EN.search(t)))
        plays = [r for r in rows if r.get("anim")]
        if plays:
            anim_src = os.path.join(ROOT, "content", source, "anim")
            os.makedirs(os.path.join(OUT, "deck", folder, "anim"), exist_ok=True)
            for f in [f"{r['stem']}.html" for r in plays] + ["deck.css", "deck.js", "anim.js"]:
                shutil.copyfile(os.path.join(anim_src, f), os.path.join(OUT, "deck", folder, "anim", f))
            deck_fonts = os.path.join(ROOT, "tools", "deck", "fonts")
            os.makedirs(os.path.join(OUT, "fonts"), exist_ok=True)
            for f in os.listdir(deck_fonts):
                if f.endswith(".woff2"):
                    shutil.copyfile(os.path.join(deck_fonts, f), os.path.join(OUT, "fonts", f))
        # The deck as vectors, where tools/deck/render.py printed it: an SVG a
        # slide, drawn while presenting, and one PDF of the whole to download.
        # Wix's static host list (WIX_TYPES) has no .pdf yet, so a --strict or
        # --no-word build leaves the PDF out and says so; a local preview has it.
        for f in svgs if vector else ():
            shutil.copyfile(os.path.join(web_src, f), os.path.join(OUT, "deck", folder, f))
        pdf = None
        pdfs = sorted(f for f in os.listdir(os.path.join(ROOT, "content", source)) if f.endswith(".pdf"))
        if pdfs and file_types(pdfs[:1], args.no_word)[1] and (args.strict or args.no_word):
            print(f"  !! deck/{folder}/{pdfs[0]} left out: Wix's static host list (WIX_TYPES) "
                  f"has no .pdf, so the Download PDF link waits for it")
        elif pdfs:
            shutil.copyfile(os.path.join(ROOT, "content", source, pdfs[0]),
                            os.path.join(OUT, "deck", folder, pdfs[0]))
            pdf = (f"deck/{folder}/{pdfs[0]}", os.path.getsize(os.path.join(OUT, "deck", folder, pdfs[0])))
        kw = dict(slides=rows) if manifest else dict(titles=titles)
        body = mine("parts/deck.py", ready(deckpart, "render", count, src=f"deck/{folder}/",
                                           title=h1, vector=vector, pdf=pdf, **kw))
        pages[href] = (f"{head} · Korkut Kaynardag", body or wrap_page(h1, "<ol>" + "".join(
            f'<li><img src="deck/{folder}/{r["stem"]}-960.webp" width="960" height="540" '
            f'style="height:auto" loading="lazy" alt="Slide {r["label"]}"></li>'
            for r in rows) + "</ol>"))
    # The Big Picture comes after the decks: it names each by the slides just
    # counted, and a deck this build did not write gets no row there and
    # counts nowhere (ROUND6_BIGPICTURE.md 2.1). Its title and note are the
    # part's own (documents.DECKS).
    decks = {h: (*v[:2], slides[h]) for h, v in getattr(dlist, "DECKS", {}).items()
             if h in slides}
    # The Big Picture's pictures (tools/bp_art.py): one from each document and
    # deck, copied to art/ and named to the page with their sizes.
    art = {}
    art_src = os.path.join(ROOT, "content", "bigpicture")
    if os.path.isfile(os.path.join(art_src, "art.json")):
        with open(os.path.join(art_src, "art.json"), encoding="utf-8") as fh:
            art = json.load(fh)
        os.makedirs(os.path.join(OUT, "art"), exist_ok=True)
        for f, _, _ in art.values():
            shutil.copyfile(os.path.join(art_src, f), os.path.join(OUT, "art", f))
    pages["big-picture.html"] = (f"{BIG_PICTURE} · Korkut Kaynardag", page_big_picture(
        mine("parts/documents.py", ready(dlist, "render_big_picture", DOCS, decks=decks, art=art))))
    if "presentation.html" in pages:
        PAGE_SECTION["presentation.html"] = "research.html"
    for href, (title, body) in pages.items():
        with open(os.path.join(OUT, href), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(shell(href, title, body, section=PAGE_SECTION.get(href, ""),
                           mast=mast_html if href == "index.html" else "",
                           desc=PAGE_DESC.get(href) or soon_desc(href)))
    # His animated figures (content/anim/), byte for byte to anim/, for the
    # document pages to draw in place of the pictures they redraw. His words
    # in them are his, as in his documents (VERBATIM).
    import preview
    anim_src = os.path.join(ROOT, "content", "anim")
    # The figures redrawn from numerical models (nf-*, tools/numfig/) are ours,
    # not his words, and bring their printed frame and any data beside them.
    for n in sorted(os.listdir(anim_src)) if os.path.isdir(anim_src) else ():
        if n.endswith(".html") or (n.startswith("nf-") and n.endswith(ANIM_ASSETS)):
            os.makedirs(os.path.join(OUT, "anim"), exist_ok=True)
            shutil.copyfile(os.path.join(anim_src, n), os.path.join(OUT, "anim", n))
        if n.endswith(".html") and not n.startswith("nf-"):
            with open(os.path.join(anim_src, n), encoding="utf-8") as fh:
                VERBATIM.append(re.sub(r"<(script|style)\b.*?</\1>", "", fh.read(),
                                       flags=re.S | re.I))
    ANIM.update(preview.animations("../anim", anim_src))
    for slug in DOCS:
        with open(os.path.join(OUT, "doc", f"{slug}.html"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(page_doc(slug, words.get(slug),
                              pending=args.no_word and slug in HOSTED_DOCX and slug not in words))
    # his posts, each between its newer and older neighbours
    said = {}
    os.makedirs(os.path.join(OUT, "post"), exist_ok=True)
    for k, post in enumerate(posts if blog else []):
        newer = posts[k - 1] if k else None
        older = posts[k + 1] if k + 1 < len(posts) else None
        page, said[f"post/{post['slug']}.html"] = post_page(
            post, OUT, args.no_word,
            newer and (f"{newer['slug']}.html", newer["title"]),
            older and (f"{older['slug']}.html", older["title"]), blog)
        with open(os.path.join(OUT, "post", f"{post['slug']}.html"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(page)

    # The pictures, once the pages have said how each is drawn (preview.USAGE).
    # A figure has a frame and a link to its full file, which a browser shows
    # on its own dark ground, so it is flattened onto white: the white panels
    # half of the transparent diagrams hold then read as one sheet, not as
    # white boxes on the warm paper. A picture drawn bare - in a table, a row
    # of steps, a sentence - keeps its transparent ground and sits on the page.
    import preview
    made = 0
    for slug in DOCS:
        src = os.path.join(BUILD, slug, "figures")
        if not os.path.isdir(src):
            continue
        dst = os.path.join(OUT, "fig", slug)
        os.makedirs(dst, exist_ok=True)
        for n in sorted(os.listdir(src)):
            stem = os.path.splitext(n)[0]
            usage = preview.USAGE.get(f"../fig/{slug}/{stem}.webp")
            if not usage:
                continue
            framed = "framed" in usage
            im = flat(os.path.join(src, n), (255, 255, 255) if framed else False)
            web(im, os.path.join(dst, f"{stem}.webp"), WEB_MAX)
            made += 1
            if framed and im.width > WEB_SMALL:
                web(im, os.path.join(dst, f"{stem}-{WEB_SMALL}.webp"), WEB_SMALL)
    print(f"figures: {made} files, framed ones on white up to {WEB_MAX}px with a "
          f"{WEB_SMALL}px copy, the rest bare")

    fail = False
    files = []
    for root, _, names in os.walk(OUT):
        files += [(os.path.join(root, n), os.path.getsize(os.path.join(root, n))) for n in names]
    total = sum(s for _, s in files)
    big = [(p, s) for p, s in files if s > WIX_FILE_MAX]
    for p, s in big:
        print("  !! 3MB ustu:", p, s)
    print(f"{len(files)} dosya, {total/1e6:.2f} MB  (sinir: {WIX_FILE_MAX/1e6:.0f} MB/dosya, "
          f"{WIX_SITE_MAX/1e6:.0f} MB/site) 3MB-ustu={len(big)}")
    if total > WIX_SITE_MAX:
        print(f"  !! site {total/1e6:.2f} MB, {WIX_SITE_MAX/1e6:.0f} MB sinirinin ustunde")
    fail |= bool(big) or total > WIX_SITE_MAX
    # where the weight is: the gallery, the posts, the rest
    share = {}
    for p, n in files:
        top = os.path.relpath(p, OUT).replace(os.sep, "/").split("/")[0]
        key = top if top in ("gallery", "post", "fig", "doc") else "pages"
        share[key] = share.get(key, 0) + n
    print("  weight: " + ", ".join(f"{k} {v / 1e6:.2f} MB" for k, v in
                                   sorted(share.items(), key=lambda kv: -kv[1])))

    # Wix's static host takes only its own list of types (WIX_TYPES). A .docx
    # is a local preview's; the build that goes to Wix (--no-word) has none.
    local, bad = file_types([p for p, _ in files], args.no_word)
    if local:
        print(f"types: {len(local)} .docx for this local preview only; Wix rejects .docx, "
              f"so the upload is built with --no-word")
    for p in bad:
        print(f"  !! Wix's static host rejects {os.path.relpath(p, OUT)}")
    print(f"types: {len(files) - len(local) - len(bad)} of {len(files)} files of a type Wix takes")
    if bad and args.strict:
        print("--strict: a file Wix rejects, build reddedildi")
        fail = True

    # No published picture keeps camera metadata (his photos' GPS positions).
    tagged = metadata_report(OUT)
    for p in tagged:
        print(f"  !! {p} still carries camera metadata")
    print(f"metadata: {len(tagged)} pictures with EXIF, XMP or GPS")
    if tagged and args.strict:
        print("--strict: camera metadata published, build reddedildi")
        fail = True

    # His gallery captions and his posts' paragraphs, word for word on their
    # pages (whitespace aside: Wix broke his captions over lines).
    def reads(href):
        with open(os.path.join(OUT, href), encoding="utf-8") as fh:
            return _words(re.sub(r"<(script|style)\b.*?</\1>", "", fh.read(), flags=re.S))
    wanted = {"gallery.html": [" ".join(ln for ln in st["lines"]) for st in sets]}
    wanted.update(said)
    missing = [(href, w) for href, ws in wanted.items() if ws
               for w in ws if " ".join(w.split()) not in reads(href)]
    count = sum(len(ws) for ws in wanted.values())
    print(f"his text: {count - len(missing)} of {count} gallery captions and post paragraphs "
          f"word for word on their pages")
    for href, w in missing:
        print(f"  !! {href}: not on the page word for word: {w[:90]!r}")
    if missing and args.strict:
        print("--strict: his gallery or blog text changed, build reddedildi")
        fail = True

    # His own sentences, each PROF_ block character for character on its page.
    # A part that drops or rewrites one fails a --strict build.
    his = {"index.html": {"PROF_HEADER": PROF_HEADER, "PROF_INTRO": PROF_INTRO,
                          "PROF_BIO": PROF_BIO, "PROF_MOTIVATION": PROF_MOTIVATION},
           "about.html": {"PROF_ABOUT": PROF_ABOUT},
           "research.html": {"PROF_RESEARCH": PROF_RESEARCH,
                             "PROF_RESEARCH_MORE": PROF_RESEARCH_MORE}}
    lost = []
    for href, blocks in his.items():
        with open(os.path.join(OUT, href), encoding="utf-8") as fh:
            text = fh.read()
        lost += [f"{href}: {name}" for name, block in blocks.items() if block not in text]
    kept = sum(len(b) for b in his.values()) - len(lost)
    print(f"his text: {kept} of {kept + len(lost)} blocks verbatim on their pages")
    for miss in lost:
        print(f"  !! {miss} is not on the page word for word; check the part that renders it")
    if lost and args.strict:
        print("--strict: his text changed, build reddedildi")
        fail = True
    checked, astray = deck_report()
    print(f"his text: {checked - len(astray)} of {checked} passages as they stand in "
          f"{os.path.basename(DECK)}")
    for name, passage in astray:
        print(f"  !! {name}: not in its slide word for word: {passage[:90]!r}")
    if astray and args.strict:
        print("--strict: his text differs from his deck, build reddedildi")
        fail = True
    checked, astray = nav_report()
    print(f"his column: {checked - len(astray)} of {checked} titles and sub-lines as they stand "
          f"on slide {NAV_SLIDE}")
    for label in astray:
        print(f"  !! the column's {label!r} is not on his slide in these words")
    if astray and args.strict:
        print("--strict: the column's words differ from his slide, build reddedildi")
        fail = True

    # Nothing private: his personal Gmail and phone number, any other address,
    # his Word CV. This fails every build, strict or not.
    leaks = private_report(OUT)
    print(f"private: {len(leaks)} (Gmail, phone number, other addresses, the Word CV)")
    for where, what in leaks:
        print(f"  !! {where}: {what}")
    if leaks:
        print("  !! the site would publish what must stay private: build reddedildi")
        fail = True
    for name, err in PART_ERRORS:
        print(f"  !! parts/{name}.py did not load ({err}); its page used the fallback")
    if PART_ERRORS and args.strict:
        print("--strict: a part did not load, build reddedildi")
        fail = True

    dashes = emdash_report(OUT)
    em = [h for h in dashes if h[3] == "em dash"]
    ours = [h for h in em if h[0] == "build.py"]
    print(f"em dash: {len(em)} (build.py {len(ours)}, parts {len(em) - len(ours)}); "
          f"spaced en dash: {len(dashes) - len(em)}")
    for owner, where, ctx, kind in sorted(dashes):
        print(f"    {owner:<18} {where}: {kind}: ...{ctx}...")
    if ours:
        print("  !! build.py'nin kendi metninde em dash var: build reddedildi")
        fail = True
    elif em and args.strict:
        print(f"--strict: {len(em)} em dash, build reddedildi")
        fail = True

    broken = link_report(OUT)
    print(f"baglanti: {len(broken)} kirik")
    for b in broken:
        print("    " + b)
    if broken and args.strict:
        print("--strict: kirik baglanti, build reddedildi")
        fail = True

    # His documents are read whole: nothing but a document's own page links a
    # place inside it (ROUND5_SPEC.md section 1).
    inside = anchor_report(OUT)
    print(f"links into a document: {len(inside)} (only a document's own page may link a "
          f"place inside it)")
    for where, url in inside:
        print(f"    {where}: {url}")
    if inside and args.strict:
        print("--strict: a link into a section of a document, build reddedildi")
        fail = True
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
