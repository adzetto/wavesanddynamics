"""Soon: the page of a topic whose document is in preparation.

Two rows of the column open a page before their documents exist: Python /
Programming and Communication. The page is his label as the <h1>, his
sub-line under it, or where he wrote none one sentence of ours saying what
the topic will hold; then the state, drawn and said; then the pages already
on the site that the topic draws on.

The state is a drawing of the topic's own work, left one step short of done,
with "In preparation" standing where the next step will go:

  Python / Programming  an interpreter session. At the first prompt a
      measured vibration is typed in; its output is the same signal sampled,
      one stem a sample, each rising from zero to its value as a hairline,
      the loop, passes it; at the second prompt a comment is typed, "# In
      preparation", and the cursor waits after it.
  Communication  a result being presented. A slide draws its title and a
      measured resonance curve, and a pointer runs along the curve and rings
      its peak; beside it the next slide stands empty, dashed, and says "In
      preparation".
  anything else  a wave running into a sensor and on as samples that fade.

Each plays once as the page opens (the session in about 2.5 s, then the
cursor blinks three times and stays), only under prefers-reduced-motion:
no-preference; otherwise it stands finished. The drawings are aria-hidden;
the state's words are text.

Every link opens a whole page: a document at its top, never a section of it
(ROUND5_SPEC 1). A page whose title is a topic of the Big Picture ends with
the way back to it, at the topic's own place there
(big-picture.html#python-programming), where the page marks the arrival.
Communication is no topic there since 26 Sep 2026, so its page does not.

render(title, sub, related) takes `related` as a list of dict(href, title),
each with an optional "note"; a document's note and length, and a page's
note, are filled in here when the caller gives none.
"""

import html
import math
import re

try:                                    # the Big Picture's topics, one list for the site
    from .documents import CATEGORIES
except ImportError:                     # loaded on its own, outside the parts package
    CATEGORIES = []
try:                                    # each document's note (ours) and its length
    from .documents import _DOCS as _DOC_NOTES, _PAGES
except ImportError:
    _DOC_NOTES, _PAGES = {}, {}

__all__ = ["CSS", "JS", "render"]

_HUB = ("big-picture.html", "Big Picture of Waves and Data Analytics")

# Our notes under a page's title, where the caller gives none: the lines the
# site already says of these pages (the Big Picture's lede; the blog's and My
# Research Areas' descriptions, cut short).
_PAGE_NOTES = {
    "big-picture.html": "Every document and slide deck on this site, by topic.",
    "blog.html": "Literature reviews, methods and experiments.",
    "research.html": "SHM, NDT and sound waves, with three documents.",
}

# What a topic will hold, in a sentence of ours, where he wrote no sub-line.
_LEDES = {
    "python-programming": "Programming for waves and data: the methods of the guides "
                          "below, in Python.",
}


def _slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def _thin(pts, tol):
    """Ramer-Douglas-Peucker, iterative: the flats and gentle stretches of a
    sampled curve cost a point or two."""
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        (x1, y1), (x2, y2) = pts[i], pts[j]
        dx, dy = x2 - x1, y2 - y1
        norm = math.hypot(dx, dy) or 1.0
        far, at = 0.0, -1
        for k in range(i + 1, j):
            d = abs(dy * (pts[k][0] - x1) - dx * (pts[k][1] - y1)) / norm
            if d > far:
                far, at = d, k
        if far > tol:
            keep[at] = True
            stack += [(i, at), (at, j)]
    return [p for p, k in zip(pts, keep) if k]


def _pts(path_pts):
    return "".join(("M" if i == 0 else "L") + f"{x:g} {y:g}" for i, (x, y) in enumerate(path_pts))


# ------------------------------------------------ Python / Programming: a session
# One column of prompts, one of lines. The two drawings of the signal share
# their width (the line column's) and their x: sample k stands under the
# wave's point at x_k. They stretch to the column (preserveAspectRatio none)
# and keep their height, so every stroke is non-scaling and each sample's
# dot is a zero-length round-capped stroke, which stays round.
_W = 560                                # the line column in the drawings' units
_WAVE_H, _WAVE_Y = 40, 20
_SMP_H, _SMP_Y = 48, 24
_AMP, _LAM, _DECAY = 14, 88, _W / 1.6  # a free vibration: ~6 cycles, down to 20%


def _vib(x):
    return _AMP * math.exp(-x / _DECAY) * math.sin(2 * math.pi * x / _LAM)


def _prompt(cls=""):
    """Python's prompt, three chevrons, typed a key at a time."""
    return (f'<svg class="soonpg__pr{cls}" viewBox="0 0 30 14" width="30" height="14" '
            'aria-hidden="true" focusable="false">'
            + "".join(f'<path class="soonpg__chev" style="--c:{i}" d="M{1.5 + 10 * i:g} 2.5l4.5 4.5-4.5 4.5"/>'
                      for i in range(3)) + '</svg>')


def _session():
    wave = _pts([(round(x, 1), round(y, 2)) for x, y in
                 _thin([(x / 2, _WAVE_Y - _vib(x / 2)) for x in range(0, 2 * _W + 1)], .04)])
    xs = [8 + 11 * k for k in range(50)]
    smp = "".join(
        f'<g class="soonpg__s" style="--i:{k}"><path d="M{x} {_SMP_Y}V{_SMP_Y - _vib(x):.2f}"/>'
        f'<path class="soonpg__dot" d="M{x} {_SMP_Y - _vib(x):.2f}h0"/></g>'
        for k, x in enumerate(xs))
    box = 'preserveAspectRatio="none" aria-hidden="true" focusable="false"'
    return (
        '<div class="soonpg__repl">'
        f'{_prompt()}'
        f'<span class="soonpg__win soonpg__win--in"><span>'
        f'<svg class="soonpg__in" viewBox="0 0 {_W} {_WAVE_H}" {box}>'
        f'<path d="{wave}"/></svg></span></span>'
        f'<svg class="soonpg__out" viewBox="0 0 {_W} {_SMP_H}" {box}>'
        f'<path class="soonpg__zero" d="M0 {_SMP_Y}H{_W}"/>{smp}</svg>'
        '<span class="soonpg__scan" aria-hidden="true"><i></i></span>'
        f'{_prompt(" soonpg__pr--next")}'
        '<p class="soonpg__tag soonpg__line">'
        '<span class="soonpg__typed"><span class="soonpg__win soonpg__win--tag"><span>'
        '<span class="soonpg__hash" aria-hidden="true"># </span>In preparation</span></span>'
        '<span class="soonpg__cur" aria-hidden="true"><i></i></span></span></p>'
        '</div>')


# ------------------------------------------------ Communication: the next slide
_SW, _SH, _GAP = 200, 112, 24           # one slide, and the gap to the next
_Z = 0.06                               # the curve's damping ratio


def _frf(r):
    return 1 / math.sqrt((1 - r * r) ** 2 + (2 * _Z * r) ** 2)


def _slides():
    x0, x1, yb, top = 24, 184, 94, 48  # the plot's box: its axes at x0 and yb
    rmax = 1.9
    peak = _frf(1.0)
    pts = [(round(x0 + (x1 - x0) * i / 480, 2), round(yb - (yb - top) * _frf(rmax * i / 480) / peak, 2))
           for i in range(481)]
    curve = _pts(_thin(pts, .05))
    px, py = x0 + (x1 - x0) / rmax, top            # the peak
    # the pointer: along the curve to the peak, then once round it, and
    # down onto it
    run = _thin([p for p in pts if p[0] <= px], .05)
    loop = [(round(px + 11 * math.sin(2 * math.pi * t / 48), 2),
             round(py - 1 - 8 * math.cos(2 * math.pi * t / 48), 2)) for t in range(49)]
    pointer = _pts(run + [(px, py - 9)] + loop + [(px, py)])
    b = _SW + _GAP
    return (
        '<div class="soonpg__deck">'
        f'<svg class="soonpg__slides" viewBox="-1 -1 {2 * _SW + _GAP + 2} {_SH + 2}" '
        f'width="{2 * _SW + _GAP + 2}" height="{_SH + 2}" aria-hidden="true" focusable="false">'
        f'<rect class="soonpg__frame" x=".5" y=".5" width="{_SW - 1}" height="{_SH - 1}" rx="8"/>'
        '<path class="soonpg__title" d="M16 18.5h76"/>'
        '<path class="soonpg__title2" d="M16 28.5h44"/>'
        f'<path class="soonpg__axes" d="M{x0} {top - 8}V{yb}H{x1 + 4}"/>'
        f'<path class="soonpg__curve" pathLength="1" d="{curve}"/>'
        f'<path class="soonpg__halo" pathLength="1" d="{pointer}"/>'
        f'<path class="soonpg__ptr" pathLength="1" d="{pointer}"/>'
        f'<rect class="soonpg__next" x="{b + .5}" y=".5" width="{_SW - 1}" height="{_SH - 1}" rx="8"/>'
        '</svg>'
        '<p class="soonpg__tag soonpg__slot">In preparation</p>'
        '</div>')


# ------------------------------------------------ anything else: a signal
_BASE, _AMP2, _HALF = 24, 12, 32


def _y(x):
    k = int(x // _HALF)
    u = (x - k * _HALF) / _HALF
    return _BASE - (1 if k % 2 == 0 else -1) * 4 * _AMP2 * u * (1 - u)


def _signal():
    humps = "".join(
        f"Q{k * _HALF + _HALF / 2:g} "
        f"{_BASE + (-1 if k % 2 == 0 else 1) * 2 * _AMP2 * min(1, (k + 1) / 2):g} "
        f"{(k + 1) * _HALF:g} {_BASE}" for k in range(5))
    xs = range(178, 466, 11)
    samples = "".join(
        f'<g class="soonpg__smp" style="--i:{j}" opacity="{0.95 * (1 - j / len(xs)) ** 1.3:.2f}">'
        f'<path d="M{x} {_BASE}V{_y(x):.1f}"/><circle cx="{x}" cy="{_y(x):.1f}" r="2.1"/></g>'
        for j, x in enumerate(xs))
    return ('<svg class="soonpg__art" viewBox="0 0 480 44" width="480" height="44" '
            'aria-hidden="true" focusable="false">'
            f'<path class="soonpg__base" d="M0 {_BASE}H480"/>'
            f'<path class="soonpg__wave" pathLength="1" d="M0 {_BASE}{humps}"/>'
            f'<g class="soonpg__ring"><circle cx="166" cy="{_BASE}" r="4.6"/>'
            f'<circle cx="166" cy="{_BASE}" r="1.7"/></g>'
            f'{samples}</svg><p class="soonpg__tag">In preparation</p>')


_STATES = {"python-programming": ("soonpg__state--py", _session()),
           "communication": ("soonpg__state--talk", _slides())}
_DEFAULT = ("soonpg__state--sig", _signal())

# The site's arrow (DESIGN_BRIEF 4.1): two paths, so the shaft can draw while
# the head travels 5px.
_ARROW = ('<svg class="soonpg__go" viewBox="0 0 24 24" width="24" height="24" '
          'fill="none" stroke="currentColor" stroke-width="1.25" '
          'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
          '<path class="ar-shaft" d="M3.5 12h13"/>'
          '<path class="ar-head" d="m11.5 6.8 5.2 5.2-5.2 5.2"/></svg>')

CSS = """
/* ---------- soon: a topic in preparation ---------- */
.soonpg{--soonpg-col:30px}
.soonpg__sub{max-width:var(--measure);margin:0;font-size:21px;line-height:1.52;
  letter-spacing:-.004em;color:var(--body);text-wrap:pretty}
.soonpg__state{max-width:var(--measure);margin:44px 0 0}
/* the words of the state: the interface's sans, quiet */
.soonpg__tag{margin:0;font:400 15px/1.4 var(--sans);letter-spacing:.006em;color:var(--muted)}

/* -- Python / Programming: a session. Prompts in one column, lines in the
   next; the drawings stretch to the column and keep their height. */
.soonpg__repl{display:grid;grid-template-columns:var(--soonpg-col) minmax(0,1fr);
  column-gap:14px;row-gap:4px;align-items:center}
.soonpg__repl>.soonpg__pr{grid-area:1/1}
.soonpg__repl>.soonpg__pr--next{grid-area:3/1}
.soonpg__win--in{grid-area:1/2}
.soonpg__out{grid-area:2/2}
.soonpg__line{grid-area:3/2}
/* the loop over the samples: a hairline that crosses the signal and its
   samples as each is taken, seen only while it runs */
.soonpg__scan{grid-area:1/2/3/3;position:relative;align-self:stretch;overflow:hidden;
  pointer-events:none}
.soonpg__scan>i{position:absolute;inset:0;opacity:0}
.soonpg__scan>i::before{content:"";position:absolute;top:0;bottom:0;left:0;width:1px;
  background:var(--link)}
/* a phone keeps every other sample: four to a cycle still draw it */
@media (max-width:560px){.soonpg__s:nth-of-type(even){display:none}}
.soonpg__pr{display:block;width:30px;height:14px;fill:none;stroke:var(--muted);
  stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
.soonpg__in,.soonpg__out{display:block;width:100%;overflow:visible;fill:none;
  stroke-linecap:round;stroke-linejoin:round}
.soonpg__in{height:40px;stroke:var(--body);stroke-width:1.5}
.soonpg__out{height:48px}
.soonpg__in path,.soonpg__out path{vector-effect:non-scaling-stroke}
.soonpg__zero{stroke:var(--rule);stroke-width:1}
.soonpg__s{stroke:var(--link);stroke-width:1.5}
.soonpg__s .soonpg__dot{stroke-width:4}
/* a window that opens from the left while what is in it holds still */
.soonpg__win{display:block;overflow:hidden}
.soonpg__win>span{display:block}
.soonpg__line{display:flex;align-items:center;min-height:24px}
.soonpg__typed{position:relative;display:inline-grid;align-items:center}
.soonpg__typed>*{grid-area:1/1}
.soonpg__win--tag{white-space:nowrap}
.soonpg__hash{color:var(--line-strong)}
/* the cursor waits after the comment, in the warm: what comes next */
.soonpg__cur{display:flex;justify-content:flex-end;align-items:center;pointer-events:none}
.soonpg__cur>i{flex:none;width:2px;height:20px;margin-right:-7px;border-radius:1px;
  background:var(--accent)}

/* -- Communication: the slide that is done and the one to come. */
.soonpg__deck{position:relative;width:min(100%,504px)}
.soonpg__slides{display:block;width:100%;height:auto;overflow:visible;fill:none;
  stroke-linecap:round;stroke-linejoin:round}
.soonpg__frame{stroke:var(--line-strong);stroke-width:1}
.soonpg__title{stroke:var(--body);stroke-width:3}
.soonpg__title2{stroke:var(--line);stroke-width:2.5}
.soonpg__axes{stroke:var(--line);stroke-width:1}
.soonpg__curve{stroke:var(--link);stroke-width:1.5}
/* the pointer: a dot riding its path, a dash of no length at the end */
.soonpg__ptr,.soonpg__halo{stroke:var(--accent);stroke-dasharray:.001 2;stroke-dashoffset:-.999}
.soonpg__ptr{stroke-width:5}
.soonpg__halo{stroke-width:14;stroke-opacity:.18}
.soonpg__next{stroke:var(--line-strong);stroke-width:1;stroke-dasharray:4 5}
.soonpg__slot{position:absolute;top:0;right:0;display:grid;place-items:center;
  width:calc(100% * 200 / 426);height:100%;padding:0 12px;text-align:center}

/* -- anything else: the signal */
.soonpg__state--sig{color:color-mix(in oklab,var(--nav) 50%,var(--page))}
.soonpg__art{display:block;width:480px;max-width:100%;height:auto;overflow:visible}
.soonpg__base{fill:none;stroke:var(--rule);stroke-width:1}
.soonpg__wave{fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round}
.soonpg__smp{fill:currentColor;stroke:currentColor;stroke-width:1.25}
.soonpg__ring circle:first-child{fill:var(--page);stroke:currentColor;stroke-width:1.4}
.soonpg__ring circle+circle{fill:currentColor}
.soonpg__state--sig .soonpg__tag{margin-top:14px}

/* where the topic is already written about */
.soonpg__h{margin:56px 0 12px;font:600 16px/1.3 var(--sans);letter-spacing:.006em;
  color:var(--ink)}
.soonpg__rows{position:relative;max-width:calc(var(--measure) + 24px);margin:0 -12px;
  padding:0;list-style:none}
.soonpg__rows::before,.soonpg__item::after{content:"";position:absolute;left:12px;
  right:12px;border-top:1px solid var(--rule);
  transition:opacity var(--t-quick) var(--ease-state)}
.soonpg__rows::before{top:0}
.soonpg__item{position:relative;margin:0}
.soonpg__item::after{bottom:0}
.soonpg__row{display:grid;grid-template-columns:minmax(0,1fr) 24px;gap:0 24px;
  align-items:center;padding:16px 12px;border-radius:var(--r-sm);color:inherit;
  text-decoration:none;-webkit-tap-highlight-color:transparent;
  transition:background-color var(--t-quick) var(--ease-state)}
.soonpg__t{display:block;font:600 19px/1.35 var(--serif);color:var(--ink);text-wrap:balance}
.soonpg__n{display:block;margin-top:3px;font:400 14px/1.45 var(--sans);
  letter-spacing:.006em;color:var(--muted);text-wrap:pretty}
.soonpg__m{font-variant-numeric:lining-nums;white-space:nowrap}
.soonpg__n>.soonpg__m{margin-left:.7em}
.soonpg__m--solo{margin-left:0}
.soonpg__go{display:block;color:var(--muted);forced-color-adjust:auto;
  transition:color var(--t-quick) var(--ease-state)}

/* states, as every row on the site: the rounded fill, one step deeper on a
   press, the hairlines that touch it fading out, the arrow drawing on */
@media (hover:hover){
  .soonpg__row:hover{background-color:color-mix(in oklab,var(--ink) 5%,var(--page))}
  .soonpg__row:hover .soonpg__go{color:var(--body)}
}
.soonpg__row:focus-visible{outline:2px solid var(--focus);outline-offset:2px;
  background-color:color-mix(in oklab,var(--ink) 5%,var(--page))}
.soonpg__row:focus-visible .soonpg__go{color:var(--body)}
.soonpg__row:active{background-color:color-mix(in oklab,var(--ink) 8%,var(--page))}
@media (hover:hover) and (forced-colors:none){
  .soonpg__item:has(.soonpg__row:hover)::after,
  .soonpg__item:has(+ .soonpg__item .soonpg__row:hover)::after,
  .soonpg__rows:has(>.soonpg__item:first-child .soonpg__row:hover)::before{opacity:0}
}
.soonpg__item:has(.soonpg__row:focus-visible)::after,
.soonpg__item:has(+ .soonpg__item .soonpg__row:focus-visible)::after,
.soonpg__rows:has(>.soonpg__item:first-child .soonpg__row:focus-visible)::before{opacity:0}
/* The arrow: on hover the shaft draws over 240ms and the head slides 5px,
   60ms behind it. A key gets the end state at once, as hero.py gives it: no
   travel for a key. Asked for less motion, the arrow stands finished. */
@media (prefers-reduced-motion:no-preference){
  .soonpg__go .ar-shaft{stroke-dasharray:13;stroke-dashoffset:5;
    transition:stroke-dashoffset var(--spring-fast)}
  .soonpg__go .ar-head{transition:transform var(--spring-fast)}
  .soonpg__row:focus-visible .ar-shaft{stroke-dashoffset:0;transition:none}
  .soonpg__row:focus-visible .ar-head{transform:translateX(5px);transition:none}
}
@media (hover:hover) and (prefers-reduced-motion:no-preference){
  .soonpg__row:hover .ar-shaft{stroke-dashoffset:0;transition-duration:var(--t-mid)}
  .soonpg__row:hover .ar-head{transform:translateX(5px);
    transition:transform var(--spring-mid) 60ms}
}

/* ----------------------------------------------------------------- motion
   Added here, never clawed back: without a no-preference answer every
   drawing stands finished.

   The session, once, in the order a session runs. The prompt is typed,
   three keys 60ms apart; the vibration is typed in after it, its window
   opening in 22 steps over 700ms while the line inside holds still;
   "Enter", and the output comes back left to right, a sample every 12ms,
   each rising from zero to its value on Motion's spring as the loop's
   hairline crosses it, in step (588ms for 49 steps); the second prompt
   is typed; the comment is typed a key at a time with the cursor riding
   its end; then the cursor blinks three times, 1.1s each, and stays.
   Transforms and opacity only; the windows are HTML, so the compositor
   runs them. */
@media (prefers-reduced-motion:no-preference){
  .soonpg__chev{animation:soonpg-key 1ms linear backwards;
    animation-delay:calc(var(--soonpg-at,80ms) + var(--c) * 60ms)}
  .soonpg__pr--next{--soonpg-at:1640ms}
  .soonpg__win--in{animation:soonpg-open 700ms steps(22,end) 300ms backwards}
  .soonpg__win--in>span{animation:soonpg-hold 700ms steps(22,end) 300ms backwards}
  .soonpg__s{transform-box:view-box;transform-origin:0 24px;
    animation:soonpg-rise var(--spring-fast) backwards,soonpg-show 120ms linear backwards;
    animation-delay:calc(1060ms + var(--i) * 12ms)}
  .soonpg__scan>i{animation:soonpg-scan 588ms linear 1060ms}
  .soonpg__win--tag{animation:soonpg-open 640ms steps(16,end) 1900ms backwards}
  .soonpg__win--tag>span{animation:soonpg-hold 640ms steps(16,end) 1900ms backwards}
  .soonpg__cur{animation:soonpg-ride 640ms steps(16,end) 1900ms backwards}
  .soonpg__cur>i{animation:soonpg-key 1ms linear 1860ms backwards,
    soonpg-blink 1.1s steps(1,end) 2640ms 3}

  /* the slide, once: its title and axes are laid down, the curve is drawn
     in 640ms, then the pointer runs along it to the peak and rings it,
     1.3s, and stays there. The next slide is there from the start. */
  .soonpg__title,.soonpg__title2,.soonpg__axes{animation:soonpg-show 240ms var(--ease-state) backwards}
  .soonpg__title{animation-delay:120ms}
  .soonpg__title2{animation-delay:200ms}
  .soonpg__axes{animation-delay:280ms}
  .soonpg__curve{stroke-dasharray:1 1;animation:soonpg-draw 640ms var(--ease) 380ms backwards}
  .soonpg__ptr,.soonpg__halo{animation:soonpg-point 1300ms cubic-bezier(.45,0,.25,1) 1080ms backwards,
    soonpg-show 160ms linear 1080ms backwards}

  /* the signal draws itself once */
  .soonpg__wave{stroke-dasharray:1 1;animation:soonpg-draw 640ms var(--ease) 120ms both}
  .soonpg__ring{animation:soonpg-show var(--t-mid) var(--ease) 520ms both}
  .soonpg__smp{animation:soonpg-show 320ms var(--ease) both;
    animation-delay:calc(560ms + var(--i) * 28ms)}
}
@keyframes soonpg-key{from{opacity:0}}
@keyframes soonpg-show{from{opacity:0}}
@keyframes soonpg-open{from{transform:translateX(-100%)}}
@keyframes soonpg-hold{from{transform:translateX(100%)}}
@keyframes soonpg-ride{from{transform:translateX(-100%)}}
@keyframes soonpg-rise{from{transform:scaleY(0)}}
@keyframes soonpg-scan{
  from{transform:translateX(1.43%);opacity:0}
  6%,90%{opacity:.5}
  to{transform:translateX(97.68%);opacity:0}
}
@keyframes soonpg-blink{50%{opacity:0}}
@keyframes soonpg-draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes soonpg-point{from{stroke-dashoffset:0}}

@media (forced-colors:active){
  .soonpg__cur>i{background:CanvasText}
}
@media print{
  .soonpg__cur{display:none}
}
"""

JS = ""


def _hub(title):
    """The way back, for a page whose title is a topic of the Big Picture:
    the Big Picture at the topic's own place (Python / Programming is
    python-programming there). None for any other page."""
    slug = _slug(title)
    ids = {c["id"] for c in CATEGORIES}
    return {"href": f"{_HUB[0]}#{slug}", "title": _HUB[1]} if slug in ids else None


def _note(href):
    """Our line under a related page's title, and a document's length."""
    path = href.split("#", 1)[0]
    if path.startswith("doc/"):
        slug = path[4:-5]
        note = (_DOC_NOTES.get(slug) or ("", ""))[1]
        return note, f"{_PAGES[slug]}-page read" if slug in _PAGES else ""
    return _PAGE_NOTES.get(path, ""), ""


def _row(r):
    note, meta = (r.get("note"), "") if r.get("note") else _note(r["href"])
    sub = ""
    if note or meta:
        solo = "" if note else " soonpg__m--solo"
        sub = (f'<span class="soonpg__n">{html.escape(note, quote=False)}'
               + (f'<span class="soonpg__m{solo}">{html.escape(meta, quote=False)}</span>' if meta else "")
               + "</span>")
    return ('<li class="soonpg__item">'
            f'<a class="soonpg__row" href="{html.escape(r["href"])}"><span>'
            f'<span class="soonpg__t">{html.escape(r["title"], quote=False)}</span>{sub}'
            f'</span>{_ARROW}</a></li>')


def render(title, sub="", related=()):
    """Return the page's body: his label, his sub-line or our sentence, the
    state, and the related pages, the Big Picture last where the title is
    one of its topics."""
    slug = _slug(title)
    rows = [dict(r) for r in related or ()]
    hub = _hub(title)
    if hub and not any(r["href"].split("#")[0] == _HUB[0] for r in rows):
        rows.append(hub)
    lede = sub or _LEDES.get(slug, "")
    cls, art = _STATES.get(slug, _DEFAULT)
    related_html = ""
    if rows:
        related_html = f"""
 <section aria-labelledby="soonpg-rel">
  <h2 class="soonpg__h" id="soonpg-rel">Related</h2>
  <ul class="soonpg__rows" role="list">{"".join(_row(r) for r in rows)}</ul>
 </section>"""
    return f"""<div class="wrap soonpg">
 <h1>{html.escape(title, quote=False).replace(" / ", "&nbsp;/ ")}</h1>
 {f'<p class="soonpg__sub">{html.escape(lede, quote=False)}</p>' if lede else ""}
 <div class="soonpg__state {cls}">{art}</div>{related_html}
</div>"""
