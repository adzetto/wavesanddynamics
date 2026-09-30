"""Blog: his eight posts, blog.html and post/<slug>.html.

The posts are his Wix blog, copied from the live site by tools/wix_pull.py
(content/blog/<slug>/post.json: the Ricos body verbatim, its pictures, the
film it embeds and the file it offers). build.py renders each body through
preview.py, as it renders his documents, and hands this module the pieces.

The index is a grid of boxes, as his Wix blog showed them (he asked for the
boxes back on 26 Sep 2026, and for three to a row on 27 Sep, because more
posts are coming). Each box holds one picture of the post, then his title,
then the date and an arrow. The picture is the first figure of the post on
the quiet surface or, for a post with no figure of its own, the opening of
his text set there instead, so every box keeps the same frame and the grid
stays aligned. The whole box is the target, but the link is his title
alone, drawn over the box, so a screen reader names each link by its title
and reads the rest as the text around it.
A post page is a document page (parts/docs.py's .docpage): the crumb back to
the Blog, his title, the date, his text and pictures in the 672px column,
then the newer and older posts. His pictures are pages of Word documents; each
links to its full-size file, the only way to read small type on a phone.

The film (one post embeds a YouTube video) is a poster with a play mark: no
request goes to YouTube until the reader presses it, and then the player loads
from youtube-nocookie.com in its place. Without JavaScript the poster is a
link to the video on YouTube.
"""

import html
import re

__all__ = ["CSS", "JS", "render_index", "render_post"]

CSS = """
/* his screenshots of text, set as text (content/blog/<slug>/text/*.html) */
.typed > * + *{margin-top:1.15em}
.typed + .typed{margin-top:1.15em}
.typed:has(> .cont:first-child),.typed:has(> .refs--cont:first-child){margin-top:.4em}
.typed .eq{display:flex;align-items:center;gap:16px;margin:1.4em 0}
.typed .eq math{flex:1;font-size:1.08em}
.typed .eq__n{color:var(--muted);font-variant-numeric:tabular-nums}
.typed h3.refs{font:600 13px/1.3 var(--sans);letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);margin-top:2em}
.typed ul.refs{list-style:none;padding:0}
.typed ul.refs li{padding-left:2em;text-indent:-2em;margin:0 0 .6em;font-size:.94em}
.typed ul.refs--cont{margin-top:0}
.typed ol.refs--num{padding-left:2.2em;font-size:.94em}
.typed ol.refs--num li{margin:0 0 .6em}
.typed ul.files{list-style:none;padding:0;font:15px/1.5 var(--sans);color:var(--ink)}
.typed ul.files li{padding:6px 0;border-top:1px solid var(--rule)}
.typed:has(> .files--cont:first-child){margin-top:0}
.typed figure.shot{margin:1.6em 0}
.typed figure.shot img{display:block;max-width:100%;height:auto;margin:0 auto}
.typed figcaption{margin-top:.8em;font-size:.9em;text-align:center;color:var(--muted)}
.typed table{border-collapse:collapse;width:100%;font-size:.9em}
.typed th,.typed td{border-top:1px solid var(--rule);padding:6px 8px;text-align:left;vertical-align:top}
/* ---------- blog: the index ---------- */
/* Three boxes to a row wherever the list is 744px wide or more: the 924px
   column of a laptop, and the 749px beside the open column at 1100. The
   professor asked for three (27 Sep 2026), because more posts are coming.
   Four were measured and set aside: at 213px a box, his longest title took
   five lines and his widest figure a strip 52px high. From 488px the list
   takes two (a tablet), and below that one (a phone). The tracks auto-fill,
   so a post alone in the last row keeps one box's width, on the grid's left
   edge. The gutter is the site's 24px step: 924 = 3 x 292 + 2 x 24. */
.blog__list{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,232px),1fr));
  gap:24px;margin:40px 0 0;padding:0;list-style:none}
.blog__list>li{display:flex;min-width:0;margin:0;break-inside:avoid}
.bcard{position:relative;flex:1;display:flex;flex-direction:column;min-width:0;
  container-type:inline-size;border:1px solid var(--rule);border-radius:var(--r-lg);
  background:var(--page);
  transition:border-color var(--t-quick) var(--ease-state),
    background-color var(--t-quick) var(--ease-state),transform var(--spring-quick)}
/* The picture first on screen, after the words for a screen reader: the
   page's quiet surface at 2:1 whatever the figure's own shape, so every
   row's titles and dates align. His figures run from 1.7:1 to 3.5:1 and sit
   whole inside it, never cropped. The frame's side inset is the title's, so
   a figure as wide as the frame allows starts on the title's left edge. */
.bcard__pic{order:-1;position:relative;aspect-ratio:2/1;overflow:hidden;
  border-radius:calc(var(--r-lg) - 1px) calc(var(--r-lg) - 1px) 0 0;
  background:var(--surface);transition:background-color var(--t-quick) var(--ease-state)}
.bcard__fit{position:absolute;inset:16px 20px;display:flex;align-items:center;
  justify-content:center}
/* his figures are drawn on white paper: multiplied, the paper takes the
   surface's tone and only his lines stand on it */
.bcard__fit img{display:block;width:auto;height:auto;max-width:100%;max-height:100%;
  mix-blend-mode:multiply}
/* No figure: the opening of his text on the surface instead, centred as a
   figure is and set on the title's edge. The frame shows whole lines only
   (round(): a line either fits or waits for the post), so no word is ever
   cut, and the markup holds all of it. Where lines wait, the last one shown
   fades toward its end: a scroll timeline on the lines is active only while
   they overflow, so a sentence that fits is never faded. */
.bcard__words{position:absolute;inset:0;display:flex;flex-direction:column;
  justify-content:center;margin:0;padding:16px 20px;
  font:400 15px/1.5 var(--serif);color:var(--muted);text-wrap:pretty;
  transition:color var(--t-quick) var(--ease-state)}
.bcard__words>span{display:block;max-height:100%;max-height:round(down,100%,1lh);
  overflow:hidden}
@supports (animation-timeline:scroll()){
  .bcard__words>span{animation:blog-more linear both;animation-timeline:scroll(self)}
}
@keyframes blog-more{from,to{
  -webkit-mask:linear-gradient(#000,#000) top/100% calc(100% - 1lh) no-repeat,
    linear-gradient(90deg,#000 45%,transparent 96%) bottom/100% 1lh no-repeat;
  mask:linear-gradient(#000,#000) top/100% calc(100% - 1lh) no-repeat,
    linear-gradient(90deg,#000 45%,transparent 96%) bottom/100% 1lh no-repeat}}
.bcard__body{flex:1;display:flex;flex-direction:column;padding:14px 20px 12px}
.bcard__title{margin:0;font:600 19px/1.3 var(--serif);letter-spacing:-.006em;
  color:var(--ink);text-wrap:balance}
.bcard__title a{color:inherit;text-decoration-thickness:1px;text-underline-offset:4px;
  text-decoration-color:transparent;-webkit-tap-highlight-color:transparent;
  transition:text-decoration-color var(--t-quick) var(--ease-state)}
/* the title's link, stretched over the whole box and over its picture */
.bcard__title a::after{content:"";position:absolute;inset:-1px;z-index:1;
  border-radius:var(--r-lg)}
.bcard__foot{display:flex;align-items:center;justify-content:space-between;gap:12px;
  margin:auto 0 0;padding-top:10px}
.bcard__date{font:600 13px/1.3 var(--sans);letter-spacing:.02em;color:var(--muted);
  font-variant-numeric:lining-nums tabular-nums}
.bcard__arrow{flex:none;display:block;width:24px;height:24px;margin-right:-3px;
  color:var(--muted);forced-color-adjust:auto;
  transition:color var(--t-quick) var(--ease-state)}
/* a narrow box (three across at 1100, two on a small tablet): the insets
   and the type a step smaller, the frame the same 2:1 */
@container (width < 260px){
  .bcard__fit{inset:14px 16px}
  .bcard__words{padding:14px 16px;font-size:14px}
  .bcard__body{padding:12px 16px 10px}
  .bcard__title{font-size:17px}
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]) .bcard__fit img{mix-blend-mode:normal;border-radius:4px}
}
:root[data-theme="dark"] .bcard__fit img{mix-blend-mode:normal;border-radius:4px}

/* Under a pointer that can hover, the box lights as a card does on this
   site (DESIGN_BRIEF section 4): each surface one step toward the ink, the
   edge firmer, a 1px underline under his title, the arrow drawn. No lift,
   no shadow, no new hue. His words on the deeper surface go one step
   darker too, from --muted (4.46:1 there) to --body, so they never drop
   under 4.5:1. A key that lands on the title gets the same state at once,
   without the travel. */
@media (hover:hover) and (pointer:fine){
  .bcard:hover{border-color:var(--line);
    background-color:color-mix(in oklab,var(--ink) 4%,var(--page))}
  .bcard:hover .bcard__pic{background-color:color-mix(in oklab,var(--ink) 4%,var(--surface))}
  .bcard:hover .bcard__title a{text-decoration-color:currentColor}
  .bcard:hover :is(.bcard__words,.bcard__arrow){color:var(--body)}
}
.bcard__title a:focus-visible{outline:0}
.bcard__title a:focus-visible::after{outline:2px solid var(--focus);outline-offset:2px}
.bcard:has(.bcard__title a:focus-visible){border-color:var(--line);
  background-color:color-mix(in oklab,var(--ink) 4%,var(--page))}
.bcard:has(.bcard__title a:focus-visible) .bcard__pic{
  background-color:color-mix(in oklab,var(--ink) 4%,var(--surface))}
.bcard:has(.bcard__title a:focus-visible) .bcard__title a{text-decoration-color:currentColor}
.bcard:has(.bcard__title a:focus-visible) :is(.bcard__words,.bcard__arrow){color:var(--body)}
/* a press answers at once: each surface a step deeper still, the box a
   touch smaller */
.bcard:active{background-color:color-mix(in oklab,var(--ink) 8%,var(--page))}
.bcard:active .bcard__pic{background-color:color-mix(in oklab,var(--ink) 8%,var(--surface))}
.bcard:active .bcard__words{color:var(--body)}
@media (prefers-reduced-motion:no-preference){
  .bcard:active{transform:scale(.985)}
  .bcard .ar-shaft{stroke-dasharray:13;stroke-dashoffset:5;
    transition:stroke-dashoffset var(--spring-fast)}
  .bcard .ar-head{transition:transform var(--spring-fast)}
  .bcard:has(.bcard__title a:focus-visible) .ar-shaft{stroke-dashoffset:0;transition:none}
  .bcard:has(.bcard__title a:focus-visible) .ar-head{transform:translateX(5px);transition:none}
}
@media (hover:hover) and (pointer:fine) and (prefers-reduced-motion:no-preference){
  .bcard:hover .ar-shaft{stroke-dashoffset:0;transition-duration:var(--t-mid)}
  .bcard:hover .ar-head{transform:translateX(5px);
    transition:transform var(--spring-mid) 60ms}
}
@media (max-width:560px){ .blog__list{margin-top:32px} }

/* ---------- blog: a post ---------- */
.docpage .postdate{margin:14px 0 0;font:600 14px/1.3 var(--sans);letter-spacing:.02em;
  color:var(--muted);font-variant-numeric:lining-nums tabular-nums}
/* Wix set his paragraphs without space between them and made a blank line
   with an empty paragraph. build.py marks a paragraph followed straight by
   another (p-tight), so his lines and lists close up and his blank lines
   stay blank. */
.docpage .postbody p.p-tight{margin-bottom:0}
.docpage .postbody figure+figure{margin-top:24px}

/* the film: a poster and a play mark until pressed, then the player */
.docpage .postvid{margin:40px 0}
.docpage .postvid__a{position:relative;display:block;aspect-ratio:16/9;border-radius:var(--r-md);
  overflow:hidden;background:#141210;color:#fff;text-decoration:none;cursor:pointer;
  -webkit-tap-highlight-color:transparent}
.docpage .postvid__a img{display:block;width:100%;height:100%;object-fit:cover;border:0;
  border-radius:0;transition:filter var(--t-fast) var(--ease-state)}
.docpage .postvid__play{position:absolute;inset:0;display:grid;place-items:center;pointer-events:none}
.docpage .postvid__play svg{width:72px;height:72px;filter:drop-shadow(0 2px 14px rgba(0,0,0,.35));
  transition:transform var(--spring-quick)}
.docpage .postvid__a:active .postvid__play svg{transform:scale(.94)}
@media (hover:hover){ .docpage .postvid__a:hover img{filter:brightness(.92)} }
.docpage .postvid__a:focus-visible{outline:2px solid var(--focus);outline-offset:3px}
.docpage .postvid iframe{display:block;width:100%;aspect-ratio:16/9;height:auto;border:0;
  border-radius:var(--r-md);background:#141210}
.docpage .postvid figcaption{margin-top:12px}

/* his file: the download row his document pages use, or its waiting state */
.docpage .postfile{margin:0 0 32px}

/* ---------- newer and older ---------- */
.docpage>.postnav{grid-row:3}
.postnav{display:grid;grid-template-columns:1fr 1fr;gap:16px 32px;margin:64px 0 0;
  padding:24px 0 0;border-top:1px solid var(--rule)}
.postnav a{display:block;padding:10px 12px;margin:-10px -12px;border-radius:var(--r-sm);
  color:inherit;text-decoration:none;-webkit-tap-highlight-color:transparent;
  transition:background-color var(--t-quick) var(--ease-state)}
.postnav .pn-older{grid-column:2;text-align:right}
.postnav small{display:block;margin-bottom:4px;font:600 13px/1.3 var(--sans);letter-spacing:.02em;
  color:var(--muted)}
.postnav b{display:block;font:600 17px/1.4 var(--serif);color:var(--ink);text-wrap:balance}
@media (hover:hover){
  .postnav a:hover{background:color-mix(in oklab,var(--ink) 5%,var(--page))}
}
.postnav a:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.postnav a:active{background:color-mix(in oklab,var(--ink) 8%,var(--page))}
@media (max-width:560px){
  .postnav{grid-template-columns:1fr}
  .postnav .pn-older{grid-column:1;text-align:left}
}
@media print{ .postnav,.docpage .postvid__play{display:none} }
"""

JS = r"""
var films=document.querySelectorAll('.postvid__a[data-embed]');
[].forEach.call(films,function(a){
  a.addEventListener('click',function(e){
    if(e.button||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;
    e.preventDefault();
    var f=document.createElement('iframe');
    f.src=a.getAttribute('data-embed')+'?autoplay=1&rel=0';
    f.title=a.getAttribute('data-title')||'Video';
    f.allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
    f.referrerPolicy='strict-origin-when-cross-origin';
    f.allowFullscreen=true;
    a.replaceWith(f);
    f.focus();
  });
});
"""

ARROW = ('<svg class="bcard__arrow" viewBox="0 0 24 24" width="24" height="24" '
         'fill="none" stroke="currentColor" stroke-width="1.25" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<path class="ar-shaft" d="M3.5 12h13"/>'
         '<path class="ar-head" d="m11.5 6.8 5.2 5.2-5.2 5.2"/></svg>')

BACK = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
        'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true"><path d="m14.5 6-6 6 6 6"/></svg>')


def title(text):
    """His title as markup, a hyphenated word kept whole on its line ("Semi-
    organizing" broke at its hyphen in a balanced heading)."""
    return re.sub(r"(\w+(?:-\w+)+)", r'<span class="nw">\1</span>', html.escape(text, quote=False))


ROW = 3      # boxes to a row on a laptop (CSS above); the first row loads at once


def render_index(posts):
    """The index boxes, newest first. Each post: `href`, `title`, `date`
    (ISO), `shown` (the date as the page prints it), `lead` (his opening
    sentence, as HTML) and `pic`: the post's first figure as
    {"src", "w", "h"}, its path from blog.html and its size, or None when the
    post has none. A box shows one picture of its post, the figure or else
    his opening sentence, and never both. The first row's pictures load at
    once, the rest lazily."""
    cards = []
    for k, p in enumerate(posts):
        pic = p.get("pic")
        if pic:
            lazy = ' loading="lazy"' if k >= ROW else ""
            inner = ('<span class="bcard__fit">'
                     f'<img src="{html.escape(pic["src"])}" alt="" width="{int(pic["w"])}" '
                     f'height="{int(pic["h"])}"{lazy} decoding="async"></span>')
        else:
            inner = (f'<p class="bcard__words"><span>{p["lead"]}</span></p>'
                     if p.get("lead") else "")
        cards.append(
            '<li><div class="bcard"><div class="bcard__body">'
            f'<h2 class="bcard__title"><a href="{html.escape(p["href"])}">{title(p["title"])}</a></h2>'
            f'<p class="bcard__foot"><time class="bcard__date" datetime="{p["date"]}">'
            f'{p["shown"]}</time>{ARROW}</p></div><div class="bcard__pic">{inner}</div></div></li>')
    # role=list: WebKit drops list semantics from a list-style:none <ul>
    return f'<ul class="blog__list" role="list">{"".join(cards)}</ul>'


def render_post(heading, date, shown, body, newer=None, older=None):
    """A post page's inner HTML. `body` is his text as preview.py rendered it;
    `newer` and `older` are (href, title) or None."""
    nav = ""
    if newer or older:
        parts = []
        if newer:
            parts.append(f'<a class="pn-newer" href="{html.escape(newer[0])}"><small>Newer post'
                         f'</small><b>{title(newer[1])}</b></a>')
        if older:
            parts.append(f'<a class="pn-older" href="{html.escape(older[0])}"><small>Older post'
                         f'</small><b>{title(older[1])}</b></a>')
        nav = f'<nav class="postnav" aria-label="More posts">{"".join(parts)}</nav>'
    return f"""<div class="wrap docpage">
  <nav class="crumb" aria-label="Breadcrumb"><a href="../blog.html">{BACK}Blog</a></nav>
  <article class="docart">
  <header class="dochead"><h1>{title(heading)}</h1>
  <p class="postdate"><time datetime="{date}">{shown}</time></p></header>
  <div class="doc postbody">{body}</div>
  </article>
  {nav}
</div>"""
