# -*- coding: utf-8 -*-
"""cv: his curriculum vitae as a page (cv.html), from content/cv/cv.json.

render(cv=None) returns the page body, <div class="wrap cv"> and all; with no
argument it reads the JSON itself (load()). tools/cv_extract.py writes that
JSON from his Word CV; the schema and the design are in parts/cv.md.

The page reads like his CV and prints as one. His words are his, in his
order; what the page adds is furniture: the "Curriculum vitae" line, the
Contents list, the Save as PDF button, the short names in the Contents list,
the "Role" label his CV already uses. Serif is his voice, sans is the
interface's (DESIGN_BRIEF.md 2.1). Every date sits right, on the line it
belongs to, in the sans at 14px with lining, tabular figures, as the About
timeline sets its years. A range is two <time> fields with a closed-up en
dash between them; a grant's amount and role are fields of their own. His
name is bold in every author list.

Layout follows the width of .cv, a size container:
  860px and up  the CV in one column (--measure-wide) with the Contents
                list beside it, sticky, marking the section being read;
  under 860px   the Contents list folds into a disclosure above the CV;
  under 560px   a position's place moves under its role, beside its dates.
Print (A4 or Letter, the reader's paper): no site column, no masthead, no
footer, no Contents, no button; link addresses printed; entries kept whole;
a running head, his name and the page count in the margins, and the saved
file named "Korkut Kaynardag CV" rather than after the tab.

Motion: the Contents mark slides to the section in view (240ms, --ease) and
nothing else moves on its own. The only script watches the sections with an
IntersectionObserver (no scroll handler) and names the saved PDF. Scoped
under .cv; tokens only; no side effects on import.
"""

import html
import json
import os
import re

__all__ = ["CSS", "JS", "render", "load", "his", "SHORT"]

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "content", "cv", "cv.json")

# The Contents list's names for his longer headings: ours, short enough for a
# 180px list. Each section keeps his heading as its <h2>.
SHORT = {
    "research-interests": "Research Interests",
    "grants": "Grants and Funding",
    "conference-proceedings": "Proceedings",
    "conference-presentations": "Presentations",
    "peer-review": "Peer Review",
    "workshops-and-memberships": "Workshops and Memberships",
    "certifications": "Certifications",
}

# his name in an author list, with or without the equal-contribution star
SELF = re.compile(r"^K\.?\s?Kaynardag\*?$")

CSS = """
@font-face{font-family:"CMU Serif";src:url(fonts/cmu-serif-500-roman.woff2) format("woff2");font-weight:400;font-style:normal;font-display:block}
@font-face{font-family:"CMU Serif";src:url(fonts/cmu-serif-500-italic.woff2) format("woff2");font-weight:400;font-style:italic;font-display:block}
@font-face{font-family:"CMU Serif";src:url(fonts/cmu-serif-700-roman.woff2) format("woff2");font-weight:600 700;font-style:normal;font-display:block}
@font-face{font-family:"CMU Serif";src:url(fonts/cmu-serif-700-italic.woff2) format("woff2");font-weight:600 700;font-style:italic;font-display:block}
/* ============================== cv.html ============================== */
.cv{container:cv/inline-size}
.cv p{margin:0}
.cv :is(ol,ul).cv-list{list-style:none;margin:0;padding:0}
.cv .cv-list>li{margin:0}

/* ---------- the head: his name, where he is, the PDF and his profiles ---------- */
.cv-head{margin:0 0 44px}
.cv-kicker{margin:0 0 14px;font:600 12px/1.1 var(--sans);letter-spacing:.12em;
  text-transform:uppercase;color:var(--muted)}
.cv-head h1{margin:0}
.cv-meta{display:flex;flex-wrap:wrap;gap:4px 24px;margin:12px 0 0;font-size:16px;
  line-height:1.5;color:var(--body)}
.cv-meta a{overflow-wrap:anywhere}
.cv-actions{display:flex;flex-wrap:wrap;align-items:center;gap:12px 28px;margin:24px 0 0}

/* the page's one filled control (DESIGN_BRIEF.md 6 keeps it for the CV). It
   exists only where scripts run, since it calls print(): shown by the
   scripting media query, so nothing moves when the page's script arrives */
.cv-pdf{display:none;align-items:center;gap:8px;min-height:44px;margin:0;
  padding:0 20px 0 16px;border:0;border-radius:var(--r-pill);background:var(--accent);
  color:var(--btn-fg);font:600 15px/1.2 var(--sans);letter-spacing:.01em;cursor:pointer;
  -webkit-tap-highlight-color:transparent;
  transition:background-color var(--t-fast) var(--ease-state),transform var(--spring-fast)}
@media (scripting:enabled){.cv-pdf{display:inline-flex}}
.cv-pdf svg{flex:none;overflow:visible}
@media (hover:hover){.cv-pdf:hover{background:var(--accent-hover)}}
.cv-pdf:active{background:var(--accent-press);transform:scale(.97)}
.cv-pdf:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
/* the arrow drops toward the tray while the pointer rests on the button */
@media (hover:hover) and (prefers-reduced-motion:no-preference){
  .cv-pdf__arrow{transition:transform var(--spring-fast)}
  .cv-pdf:hover .cv-pdf__arrow{transform:translateY(2px)}
}
@media (forced-colors:active){.cv-pdf{border:1px solid ButtonText}}

.cv-links{display:flex;flex-wrap:wrap;gap:0 24px;margin:0;padding:0;list-style:none}
.cv-links li{margin:0}
.cv-links a{display:inline-flex;align-items:center;min-height:44px;
  font:600 15px/1.2 var(--sans);letter-spacing:.01em}

/* ---------- the sections ---------- */
.cv-sec{margin:48px 0 0;padding:28px 0 0;border-top:1px solid var(--rule)}
.cv-main>.cv-sec:first-child{margin-top:0}
.cv-sec>h2{margin:0 0 24px}
@media (width > 1000px){.cv-sec{scroll-margin-top:24px}}

/* a subgroup: "Published", "Workshops": his label, set as the site's eyebrow,
   with his note beside it */
.cv-group+.cv-group{margin-top:32px}
.cv-group__head{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 16px;margin:0 0 16px}
.cv-group__head h3{margin:0;font:600 12px/1.1 var(--sans);letter-spacing:.12em;
  text-transform:uppercase;color:var(--muted)}
.cv-note{font-size:16px;line-height:1.5;color:var(--muted)}

/* ---------- an entry ----------
   What it is on the left, when it was on the right, on the first line's
   baseline. Titles 19px in --ink; the lines under them 16px. */
.cv-e{display:grid;grid-template-columns:minmax(0,1fr) auto;column-gap:32px;
  align-items:baseline;padding:0 0 20px}
.cv-e:last-child{padding-bottom:0}
.cv-t{grid-area:t;font-size:19px;line-height:1.4;font-weight:600;color:var(--ink);
  text-wrap:pretty}
.cv-s{grid-area:s;margin-top:2px;font-size:16px;line-height:1.5;color:var(--body);
  text-wrap:pretty}
.cv-in{grid-area:in;font-size:16px;line-height:1.5;color:var(--muted);text-wrap:pretty}
.cv-when,.cv-where,.cv-amt{justify-self:end;text-align:right;white-space:nowrap;
  font:600 14px/1.5 var(--sans);letter-spacing:.01em;color:var(--muted);
  font-variant-numeric:lining-nums tabular-nums}
.cv-when{grid-area:when}
.cv-where{grid-area:where}
.cv-amt{grid-area:amt;color:var(--ink)}
.cv-to{padding:0 .1em}

/* a position: organisation and place, then role and dates, as his CV sets them */
.cv-pos{grid-template-areas:"t where" "s when"}
/* a grant: title and years, the line under it and the amount, then his role */
.cv-grant{grid-template-areas:"t when" "s amt" "role role"}
.cv-role{grid-area:role;margin-top:6px;font-size:16px;line-height:1.5;color:var(--body)}
.cv-lbl{margin-right:10px;font:600 12px/1.1 var(--sans);letter-spacing:.12em;
  text-transform:uppercase;color:var(--muted)}
/* an award, a certificate, a patent, a workshop: title, date, and a line. A
   list whose every entry has a line under its title sets the titles in 600,
   as his CV bolds them; any other list keeps them all at 400 */
.cv-item{grid-template-areas:"t when" "s s"}
.cv-list--plain .cv-t{font-weight:400}

/* a paper or a talk: title, then the authors, then where it appeared; the year
   on the title's line. Numbered where his CV numbers them, in a gutter. */
.cv-cite{grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"t when" "by by" "in in"}
.cv-cite .cv-t{font-weight:400}
.cv-by{grid-area:by;margin-top:4px;font-size:16px;line-height:1.5;color:var(--body)}
.cv-me{font-weight:600;color:var(--ink)}
.cv-list>.cv-cite{padding-bottom:24px}
.cv-list>.cv-cite:last-child{padding-bottom:0}
.cv-list--num{counter-reset:cv}
.cv-list--num>.cv-cite{counter-increment:cv;column-gap:0;
  grid-template-columns:36px minmax(0,1fr) 32px auto;
  grid-template-areas:"n t . when" ". by by by" ". in in in"}
.cv-list--num>.cv-cite::before{content:counter(cv);grid-area:n;
  font:600 14px/1.5 var(--sans);letter-spacing:.01em;color:var(--muted);
  font-variant-numeric:lining-nums tabular-nums}

/* his research areas: his table, three columns read downward (his first
   column is the monitoring, the second the dynamics and the data, the third
   the modelling), a hairline over each cell and each row as tall as its
   tallest cell, so the rules run straight across */
.cv-areas{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
  grid-template-rows:repeat(var(--cv-rows,5),auto);grid-auto-flow:column;column-gap:24px;
  margin:0;padding:0;list-style:none}
.cv-areas li{margin:0;padding:10px 0 12px;border-top:1px solid var(--rule);
  font-size:16px;line-height:1.45;color:var(--ink)}

/* ---------- Contents: beside the CV on a wide page, folded above it on a
   narrow one. The mark is the docs' own: one warm line on a hairline track,
   sliding to the section in view ---------- */
.cv-rail{display:none}
.cv-toc-nav{margin:0 0 40px}
.cv-toc{border-block:1px solid var(--rule)}
.cv-toc__sum{display:flex;align-items:center;gap:8px;min-height:48px;margin:0 -12px;
  padding:0 12px;border-radius:var(--r-sm);list-style:none;cursor:pointer;
  -webkit-tap-highlight-color:transparent;
  transition:background-color var(--t-quick) var(--ease-state)}
.cv-toc__sum::-webkit-details-marker{display:none}
.cv-toc__h,.cv-rail__h{font:600 12px/1.1 var(--sans);letter-spacing:.12em;
  text-transform:uppercase;color:var(--muted)}
.cv-toc__chev{flex:none;color:var(--muted);transition:transform var(--spring-fast)}
.cv-toc[open] .cv-toc__chev{transform:rotate(90deg)}
.cv-toc__sum:focus-visible{outline:2px solid var(--focus);outline-offset:-2px}
@media (hover:hover){.cv-toc__sum:hover{background:color-mix(in oklab,var(--ink) 5%,var(--page))}}
.cv-toc__sum:active{background:color-mix(in oklab,var(--ink) 8%,var(--page))}
.cv-toc ol{columns:2 150px;column-gap:24px;margin:4px 0 12px;padding:0;list-style:none}
.cv-toc li{break-inside:avoid;margin:0}
.cv-toc a{display:flex;align-items:center;min-height:44px;font-size:16px;line-height:1.3;
  color:var(--body);text-decoration:none}
@media (hover:hover){.cv-toc a:hover{color:var(--ink);text-decoration:underline;
  text-decoration-color:color-mix(in oklab,currentColor,transparent 62%)}}

@container cv (min-width:860px){
  .cv-toc-nav{display:none}
  .cv-body{display:grid;grid-template-columns:minmax(0,var(--measure-wide)) 180px;
    column-gap:32px;justify-content:space-between;align-items:start}
  .cv-main{grid-column:1;grid-row:1}
  .cv-rail{grid-column:2;grid-row:1;display:block;position:sticky;top:40px;
    max-height:calc(100vh - 80px);overflow-y:auto;overscroll-behavior:contain;
    scrollbar-width:thin}
  .cv-rail__h{display:block;margin:0 0 12px 16px}
  .cv-rail__track{position:relative}
  .cv-rail ol{margin:0;padding:0;list-style:none;border-left:1px solid var(--rule)}
  .cv-rail li{margin:0}
  .cv-rail a{display:block;padding:5px 4px 5px 15px;font-size:15px;line-height:1.35;
    color:var(--muted);text-decoration:none;border-radius:0 var(--r-sm) var(--r-sm) 0;
    transition:color var(--t-quick) var(--ease-state)}
  .cv-rail a[aria-current]{color:var(--ink)}
  @media (hover:hover){.cv-rail a:hover{color:var(--ink)}}
  .cv-rail a:focus-visible{outline:2px solid var(--focus);outline-offset:-2px}
  .cv-rail__mark{position:absolute;top:0;left:0;width:2px;height:1px;
    background:var(--accent);transform-origin:0 0;opacity:0;pointer-events:none}
  .cv-rail__mark.is-on{opacity:1}
}
@media (prefers-reduced-motion:no-preference){
  .cv-rail__mark{transition:transform var(--spring-mid),
    opacity var(--t-fast) var(--ease-state)}
}
@media (forced-colors:active){
  .cv-rail__mark{width:0;background:none;border-left:2px solid Highlight}
}

/* under 860px the folded Contents list carries the rules above the CV */
@container cv (width < 860px){
  .cv-main>.cv-sec:first-child{border-top:0;padding-top:0}
}

/* ---------- narrow: a position's place drops under its role ---------- */
@container cv (width < 560px){
  .cv-pos{grid-template-areas:"t t" "s s" "where when";column-gap:16px}
  .cv-pos .cv-where{justify-self:start;text-align:left;white-space:normal}
  .cv-e{column-gap:16px}
  .cv-list--num>.cv-cite{grid-template-columns:28px minmax(0,1fr) 16px auto}
  .cv-areas{grid-template-columns:minmax(0,1fr);grid-template-rows:none;grid-auto-flow:row}
}

/* ---------- print: his CV on paper, A4 or Letter ----------
   The page takes the reader's paper size and a margin both sizes carry.
   Everything that is a screen's furniture goes; the text keeps its own
   hierarchy at print sizes; an entry never breaks across two pages and a
   heading never ends one. Link addresses are printed after the links.
   The margins carry a running head and the page count. Chrome draws its own
   date, title and address there unless the page fills those corners with
   visible text (an empty string does not count), so the PDF comes out the
   same whether or not "Headers and footers" is ticked. A named page, so
   printing any other page of the site keeps the browser's own margins. */
@page cv{margin:15mm 16mm 16mm;
  @top-right{content:"Curriculum Vitae";font:italic 9pt/1 "CMU Serif",serif;color:#444}
  @bottom-left{content:"Korkut Kaynardag";font:9pt/1 "CMU Serif",serif;color:#444}
  @bottom-right{content:counter(page) " / " counter(pages);font:9pt/1 "CMU Serif",serif;color:#444}}
@media print{
  .cv{page:cv;max-width:none;margin:0;padding:0;font-size:10pt;line-height:1.38}
  body:has(.cv) :is(.skip,.foot,.bar,.side,.fold){display:none!important}
  body:has(.cv),body:has(.cv) .main{min-height:0;margin:0;background:none}
  .cv-kicker,.cv-pdf,.cv-toc-nav,.cv-rail{display:none!important}
  .cv a{color:inherit;text-decoration:none}
  .cv-head{margin:0 0 12pt}
  .cv-head h1{font-size:20pt;line-height:1.15}
  .cv-meta{margin-top:4pt;font-size:10pt;gap:0 14pt}
  .cv-actions{display:block;margin-top:6pt}
  .cv-links{display:block}
  .cv-links li{display:block}
  .cv-links a{display:grid;grid-template-columns:72pt minmax(0,1fr);column-gap:10pt;
    min-height:0;font:600 9pt/1.4 var(--sans)}
  .cv-links a::after{content:attr(href);font-weight:400;color:var(--body);
    overflow-wrap:anywhere}
  .cv-body{display:block}
  .cv-sec{margin:12pt 0 0;padding:6pt 0 0;border-top:.75pt solid var(--line-strong)}
  .cv-sec>h2{margin:0 0 6pt;font-size:12pt;line-height:1.2;break-after:avoid}
  .cv-group+.cv-group{margin-top:8pt}
  .cv-group__head{margin:0 0 5pt;break-after:avoid}
  .cv-group__head h3{font-size:8pt}
  .cv-note{font-size:9pt}
  .cv-e{padding-bottom:6pt;column-gap:14pt;break-inside:avoid}
  .cv-t{font-size:10.5pt;line-height:1.3}
  .cv-s,.cv-by,.cv-in,.cv-role,.cv-areas li{font-size:9.5pt;line-height:1.35}
  .cv-when,.cv-where,.cv-amt{font-size:8.5pt;line-height:1.5}
  .cv-lbl{font-size:7.5pt}
  .cv-list--num>.cv-cite{grid-template-columns:22pt minmax(0,1fr) 12pt auto}
  .cv-list--num>.cv-cite::before{font-size:8.5pt}
  .cv-areas{column-gap:14pt}
  .cv-areas li{padding:3pt 0 4pt}
  .cv-list>.cv-cite{padding-bottom:6pt}
  .cv p,.cv li{orphans:3;widows:3}

  /* LaTeX look: Computer Modern throughout, a centred title block, small-caps
     section heads over a hairline, margins of an article class page */
  .cv,.cv *{font-family:"CMU Serif","Latin Modern Roman",serif!important;color:#000!important;
    letter-spacing:0!important}
  .cv-head{text-align:center;margin:0 0 10pt}
  .cv-head h1{font-size:22pt;font-weight:400;letter-spacing:.02em!important}
  .cv-meta{justify-content:center;font-size:10pt}
  .cv-links a{font:400 9pt/1.4 "CMU Serif",serif!important;display:inline;margin:0 6pt}
  .cv-links a::after{content:none}
  .cv-links,.cv-links li{display:inline}
  .cv-actions{text-align:center}
  .cv-sec{border-top:0;padding-top:0;margin-top:14pt}
  .cv-sec>h2{font-size:12pt;font-weight:400;font-variant:small-caps;letter-spacing:.06em!important;
    border-bottom:.5pt solid #000;padding-bottom:2pt;margin-bottom:7pt}
  .cv-group__head h3{font-size:10pt;font-weight:700;font-variant:normal;text-transform:none}
  .cv-t{font-weight:700;font-size:10.5pt}
  .cv-when,.cv-where,.cv-amt{font-size:9.5pt;font-style:italic}
  .cv-lbl{font-size:9pt;font-variant:small-caps;text-transform:none}
  .cv-me{font-weight:700}
  .cv-in{font-style:italic}
  .cv-list--num>.cv-cite::before{font-family:"CMU Serif",serif!important;font-size:9.5pt}
}
"""

# One observer marks the section in view in the Contents list (the band is
# the top third of the window, so a heading is marked as it arrives at
# reading height), and the saved PDF is named for him, not for the tab.
JS = """
var cv=document.querySelector('.cv');
if(!cv)return;
if(document.fonts)['400 10pt','italic 400 10pt','700 10pt','italic 700 10pt'].forEach(function(f){document.fonts.load(f+' "CMU Serif"')});
var head=cv.querySelector('[data-pdf-name]'),title=document.title,
  name=head&&head.getAttribute('data-pdf-name');
if(name){
  addEventListener('beforeprint',function(){document.title=name;});
  addEventListener('afterprint',function(){document.title=title;});
}
var rail=cv.querySelector('.cv-rail');
if(!rail||!('IntersectionObserver' in window))return;
var mark=rail.querySelector('.cv-rail__mark'),links={},on={},cur=null,
  secs=[].slice.call(cv.querySelectorAll('.cv-sec'));
[].forEach.call(rail.querySelectorAll('a'),function(a){links[a.hash.slice(1)]=a;});
function place(){
  var a=cur&&links[cur];
  if(!a||!a.offsetParent){mark.classList.remove('is-on');return;}
  mark.style.transform='translateY('+a.offsetTop+'px) scaleY('+a.offsetHeight+')';
  mark.classList.add('is-on');
}
function show(id){
  if(id===cur)return;
  if(cur&&links[cur])links[cur].removeAttribute('aria-current');
  cur=id;
  if(cur&&links[cur])links[cur].setAttribute('aria-current','true');
  place();
}
var io=new IntersectionObserver(function(es){
  es.forEach(function(e){on[e.target.id]=e.isIntersecting;});
  for(var i=0;i<secs.length;i++)if(on[secs[i].id])return show(secs[i].id);
  show(null);
},{rootMargin:'0px 0px -66% 0px'});
secs.forEach(function(s){io.observe(s);});
addEventListener('resize',place,{passive:true});
"""

# the inline icon family: a 24-unit grid drawn at 20px, stroke 1.5
# (build.py's "download" glyph, its arrow a path of its own so it can move)
_SAVE = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
         'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<path class="cv-pdf__arrow" d="M12 5v10m-4.5-4.5L12 15l4.5-4.5"/>'
         '<path d="M6 19h12"/></svg>')
_CHEV = ('<svg class="cv-toc__chev" viewBox="0 0 24 24" width="20" height="20" fill="none" '
         'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
         'stroke-linejoin="round" aria-hidden="true"><path d="m9.5 6 6 6-6 6"/></svg>')


def load(path=DATA):
    """cv.json as a dict (tools/cv_extract.py writes it from his Word CV)."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _t(s):
    return html.escape(str(s), quote=False)


def _iso(d):
    """09/2016 -> 2016-09; 2017 -> 2017."""
    m = re.fullmatch(r"(\d{2})/(\d{4})", d)
    return f"{m.group(2)}-{m.group(1)}" if m else d


def _time(d):
    return _t(d) if not re.fullmatch(r"\d{2}/\d{4}|\d{4}", d) else \
        f'<time datetime="{_iso(d)}">{_t(d)}</time>'


def _when(e):
    if e.get("start"):
        return (f'<p class="cv-when">{_time(e["start"])}<span class="cv-to">&#8211;</span>'
                f'{_time(e["end"])}</p>')
    if e.get("date"):
        return f'<p class="cv-when">{_time(e["date"])}</p>'
    return ""


def _authors(names):
    return ", ".join(f'<b class="cv-me">{_t(n)}</b>' if SELF.match(n) else _t(n) for n in names)


def _entry(e):
    kind = e.get("type")
    if kind == "position":
        return (f'<li class="cv-e cv-pos"><p class="cv-t">{_t(e["org"])}</p>'
                f'<p class="cv-where">{_t(e["place"])}</p>'
                f'<p class="cv-s">{_t(e["role"])}</p>{_when(e)}</li>')
    if kind == "grant":
        return ('<li class="cv-e cv-grant">'
                f'<p class="cv-t">{_t(e["title"])}</p>{_when(e)}'
                + (f'<p class="cv-s">{_t(e["line"])}</p>' if e.get("line") else "")
                + (f'<p class="cv-amt">{_t(e["amount"])}</p>' if e.get("amount") else "")
                + (f'<p class="cv-role"><span class="cv-lbl">Role</span>{_t(e["role"])}</p>'
                   if e.get("role") else "")
                + "</li>")
    if kind == "citation":
        return ('<li class="cv-e cv-cite">'
                f'<p class="cv-t">{_t(e["title"])}</p>'
                f'<p class="cv-when"><time datetime="{_t(e["year"])}">{_t(e["year"])}</time></p>'
                + (f'<p class="cv-by">{_authors(e["authors"])}</p>' if e.get("authors") else "")
                + (f'<p class="cv-in">{_t(e["venue"])}</p>' if e.get("venue") else "")
                + "</li>")
    if kind == "item":
        detail = e.get("detail")
        return ('<li class="cv-e cv-item">'
                f'<p class="cv-t">{_t(e["title"])}</p>{_when(e)}'
                + (f'<p class="cv-s">{_t(detail)}</p>' if detail else "") + "</li>")
    raise ValueError(f"parts/cv.py: an entry of no known type: {e!r}")


def _list(box):
    """A section's or a group's entries: the areas as his table, the rest as a list."""
    entries = [e for e in box["entries"] if e.get("type") != "group"]
    if not entries:
        return ""
    if all(e.get("type") == "area" for e in entries):
        rows = -(-len(entries) // 3)
        return (f'<ul class="cv-areas" role="list" style="--cv-rows:{rows}">'
                + "".join(f"<li>{_t(e['text'])}</li>" for e in entries) + "</ul>")
    tag = "ol" if box.get("numbered") else "ul"
    cls = "cv-list" + (" cv-list--num" if box.get("numbered") else "")
    if any(e.get("type") == "item" for e in entries) and not all(e.get("detail") for e in entries):
        cls += " cv-list--plain"
    return (f'<{tag} class="{cls}" role="list">'
            + "".join(_entry(e) for e in entries) + f"</{tag}>")


def _group(g):
    note = f'<p class="cv-note">{_t(g["note"])}</p>' if g.get("note") else ""
    return (f'<div class="cv-group"><div class="cv-group__head"><h3>{_t(g["title"])}</h3>'
            f'{note}</div>{_list(g)}</div>')


def _section(s):
    sid = _t(s["id"])
    parts, run = [], []
    for e in s["entries"]:          # entries before, between and after groups, in order
        if e.get("type") == "group":
            if run:
                parts.append(_list({"entries": run, "numbered": s.get("numbered")}))
                run = []
            parts.append(_group(e))
        else:
            run.append(e)
    if run:
        parts.append(_list({"entries": run, "numbered": s.get("numbered")}))
    return (f'<section class="cv-sec" id="{sid}" aria-labelledby="{sid}-h">'
            f'<h2 id="{sid}-h">{_t(s["title"])}</h2>{"".join(parts)}</section>')


def _index(sections):
    return "".join(f'<li><a href="#{_t(s["id"])}">{_t(SHORT.get(s["id"], s["title"]))}</a></li>'
                   for s in sections)


def render(cv=None):
    """The CV page's body from cv.json's dict (None: read content/cv/cv.json)."""
    cv = load() if cv is None else cv
    sections = cv.get("sections") or []
    email = cv.get("email", "")
    user, _, host = email.partition("@")
    meta = (f'<p class="cv-meta"><span>{_t(cv.get("location", ""))}</span>'
            + (f'<a href="mailto:{html.escape(email)}">{_t(user)}@<wbr>{_t(host)}</a>'
               if email else "") + "</p>")
    links = "".join(f'<li><a href="{html.escape(ln["href"])}" rel="me">{_t(ln["label"])}</a></li>'
                    for ln in cv.get("links") or [])
    links = (f'<ul class="cv-links" role="list" aria-label="Profiles">{links}</ul>'
             if links else "")
    index = _index(sections)
    pdf_name = html.escape(cv.get("name", "").split(",")[0].strip() + " CV")
    return (
        '<div class="wrap cv">'
        f'<header class="cv-head" data-pdf-name="{pdf_name}">'
        '<p class="cv-kicker">Curriculum vitae</p>'
        f'<h1>{_t(cv.get("name", ""))}</h1>{meta}'
        '<div class="cv-actions">'
        f'<button class="cv-pdf" type="button" onclick="print()">{_SAVE}Save as PDF</button>'
        f'{links}</div></header>'
        '<nav class="cv-toc-nav" aria-labelledby="cv-toc-h">'
        '<details class="cv-toc"><summary class="cv-toc__sum">'
        f'<span class="cv-toc__h" id="cv-toc-h">Contents</span>{_CHEV}</summary>'
        f'<ol role="list">{index}</ol></details></nav>'
        # the list beside the CV comes first, so a screen reader meets the
        # contents before the sections, as it does on a narrow page
        '<div class="cv-body"><nav class="cv-rail" aria-labelledby="cv-rail-h">'
        '<span class="cv-rail__h" id="cv-rail-h">Contents</span>'
        f'<div class="cv-rail__track"><ol role="list">{index}</ol>'
        '<span class="cv-rail__mark" aria-hidden="true"></span></div></nav>'
        '<div class="cv-main">' + "".join(_section(s) for s in sections)
        + '</div></div></div>')


def his(cv=None):
    """His words as the page prints them (HTML-escaped), for build.py's VERBATIM
    list, so the em dash report bills none of them to this part (one title of
    his carries a spaced en dash)."""
    cv = load() if cv is None else cv
    out = []

    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if k not in ("type", "id", "kind", "href", "numbered"):
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str) and v.strip():
            out.append(_t(v))

    walk(cv.get("sections") or [])
    return sorted(set(out), key=len, reverse=True)
