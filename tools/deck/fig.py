"""The deck's figures: computed in Python, drawn as pgfplots and TikZ draw them.

A figure is a Fig: an SVG at 1:1 in slide pixels (the slide is 1920 x 1080)
with its words as HTML laid over it, so his labels and the maths in them set
exactly as the slide's text does (<m>..</m> works inside any label). A slide
asks for one with <div data-fig="name"></div>; render.py calls name() in the
slide's own script, tools/deck/src/sNNN.py, and puts the returned HTML there.

    from fig import Fig, C
    f = Fig(1000, 600)
    ax = f.axes(110, 20, 860, 470, xlim=(0, 25), ylim=(0, 100),
                xticks=[0, 3, 10, 15, 20, 25], yticks=range(0, 101, 20),
                xlabel="Number inspected without replacement",
                ylabel="Chance of finding the defect (%)", grid=True)
    ax.plot(k, 100 * k / 25, color=C.navy)
    ax.mark(3, 12)                              # the operating point, in the accent
    ax.text(10, 20, "3 inspected: 12%", "south west", color=C.accent)
    return f.html()

The look (tools/numfig/README.md, scaled to the slide): a full box axis in ink,
2 px; ticks inward, 10 px, on all four sides; numeric tick labels in Computer
Modern 24 px; axis labels 26 px; data 4 px (secondary 3 px); guides 1.5 px
dashed in C.guide; a light grid only where values are read. Blues for the model
and the data, the accent for the one thing the eye must follow. No gradients,
no shadows, no rounded boxes.

Every number drawn comes from the model the slide states (numpy, scipy): a
curve is its function sampled finely enough to be smooth at 1:1, a sample is a
deterministic low-discrepancy draw from the stated distribution (sample()),
never hand-placed points.

Animation (DECK_BRIEF.md "Animated slides"). Every drawing call takes anim=,
how the mark arrives while the slide plays: draw(t0, dur), pop(t0), fade(t0,
dur), wipe(t0, dur), grow(t0, dur, stagger), seq(t0, dt) and keys(times,
values), combined with + (pop(1) + keys(...)). Times are seconds from the
figure's start. The spec is written as data (data-anim) that the static slide
ignores, so the picture is the same with or without it; anim.js plays it. A
mark drawn with ghost=True shows only while the slide plays (the 25 tests
that become their average), and never in the picture.
"""

import html as _html
import json as _json
import math

import numpy as np


# ------------------------------------------------------------------ animation
# How a mark arrives while the slide plays (anim.js runs it; DECK_BRIEF.md
# "Animated slides"). A spec is data: its times are seconds from the start of
# the figure it is in, and .end is when it has arrived, to start the next
# thing from (draw(...).end + 0.2).

def spring_done(visual):
    """Seconds until Motion's spring (bounce 0) of this visual duration is at
    rest: its value within 0.005 of the target and its speed under 0.01 a
    second, as motion 12.43.0's spring() decides (anim.js settle())."""
    w = 2 * math.pi / (1.2 * visual)
    t = visual
    while True:
        x = w * t
        if math.exp(-x) * (1 + x) <= 0.005 and w * w * t * math.exp(-x) <= 0.01:
            return round(t, 3)
        t += 0.001


def _r(v, nd=3):
    """A number for data-anim, short."""
    v = round(float(v), nd)
    return int(v) if v == int(v) else v


class Spec:
    """One animation of a mark: a kind, a start t (seconds from the
    figure's start) and its parameters. For a call that draws several marks
    (scatter, bars ...), dt or times give each mark its own start."""

    SPRING = {"pop", "grow"}

    def __init__(self, kind, t=0.0, dt=0.0, times=None, n=None, **kw):
        self.kind, self.t, self.dt, self.times, self.n, self.kw = kind, float(t), float(dt), times, n, kw

    # when it has arrived (to compose from), and when it is exactly at rest
    def _span(self, i):
        t = self.times[i] if self.times is not None else self.t + i * self.dt
        if self.kind == "keys":
            last = self.kw["t"][-1]
            vd = self.kw.get("vd", 0.3) if self.kw.get("e", "settle") == "settle" else 0.0
            return last, last + vd, last + (spring_done(vd) if vd else 0.0)
        if self.kind in self.SPRING:
            v = self.kw["v"]
            return t, t + v, t + spring_done(v)
        return t, t + self.kw["d"], t + self.kw["d"]

    def _last(self):
        if self.times is not None:
            return len(self.times) - 1
        if self.dt:
            if self.n is None:
                raise ValueError("a seq's end is known once it has been drawn (or give it n=)")
            return self.n - 1
        return 0

    @property
    def end(self):
        return self._span(self._last())[1]

    @property
    def done(self):
        return self._span(self._last())[2]

    def bind(self, n):
        """A call that draws n marks tells its spec how many."""
        if self.times is not None and len(self.times) != n:
            raise ValueError(f"seq has {len(self.times)} times for {n} marks")
        self.n = n
        return self

    def at(self, i):
        """The spec of the i-th mark of a call."""
        if self.times is None and not self.dt:
            return self
        t = self.times[i] if self.times is not None else self.t + i * self.dt
        return Spec(self.kind, t, **self.kw)

    def json(self):
        d = {"k": self.kind, "t": _r(self.t)}
        for k, v in self.kw.items():
            d[k] = v if isinstance(v, (str, list)) else _r(v)
        return [d]

    def __add__(self, other):
        return Specs(self, other)

    def head(self):
        """An arrow's tip: it comes in as the line it ends arrives."""
        if self.kind == "draw":
            d = self.kw["d"]
            return Spec("fade", self.t + 0.8 * d, d=max(0.12, 0.2 * d))
        return self


class Specs:
    """Several specs on one mark, played together (pop(1) + keys(...))."""

    def __init__(self, *parts):
        self.parts = []
        for p in parts:
            self.parts += p.parts if isinstance(p, Specs) else [p]

    end = property(lambda self: max(p.end for p in self.parts))
    done = property(lambda self: max(p.done for p in self.parts))

    def bind(self, n):
        for p in self.parts:
            p.bind(n)
        return self

    def at(self, i):
        return Specs(*[p.at(i) for p in self.parts])

    def json(self):
        return [d for p in self.parts for d in p.json()]

    def __add__(self, other):
        return Specs(self, other)

    def head(self):
        return Specs(*[p.head() for p in self.parts])


def draw(t0, dur=0.6):
    """A stroke draws itself along its length (manim's Create: seg())."""
    return Spec("draw", t0, d=dur)


def pop(t0, visual=0.35):
    """A mark or a label arrives: it fades in and settles into its place
    (Motion's spring, bounce 0, `visual` seconds to arrive)."""
    return Spec("pop", t0, v=visual)


def fade(t0, dur=0.4):
    """It fades in, in place."""
    return Spec("fade", t0, d=dur)


def out(t0, dur=0.3):
    """It fades out: only for a ghost, which the picture does not have."""
    return Spec("out", t0, d=dur)


def wipe(t0, dur=0.6, dir="right"):
    """An area is uncovered from one side (right: from the left edge on;
    up: from its base)."""
    return Spec("wipe", t0, d=dur, dir=dir)


def grow(t0, dur=0.5, stagger=0.0):
    """Bars grow from their base on a spring; with stagger, bar i starts
    stagger * i later (in the order they were given)."""
    return Spec("grow", t0, dt=stagger, v=dur)


def seq(t0=0.0, dt=0.1, kind="pop", times=None, n=None, visual=0.3, dur=0.3):
    """Marks one after another, in the order drawn: mark i at t0 + i dt, or
    at times[i]. Each arrives as `kind` (pop, fade, draw, grow). On a single
    line (plot, step), the line extends through its points: point i reached
    at t0 + i dt (or times[i])."""
    kw = {"v": visual} if kind in Spec.SPRING else {"d": dur}
    return Spec(kind, t0, dt=dt, times=list(times) if times is not None else None, n=n, **kw)


def keys(times, values, prop="xy", ease="settle", visual=0.3, nd=None):
    """A value that changes over time, one keyframe at each time. The last
    value is the one the slide shows. prop:
        xy, x, y   where the mark is (Axes: data; Fig: px), moved there
        h          a bar's height (Axes: data; Fig: px), from its base
        p          how much of a stroke is drawn, 0 to 1
        o          opacity, 0 to 1
        s          scale about the mark's centre
        d          a path's data (strings of one shape: the numbers move)
        text       a number shown in the mark (a <span> in a label), nd places
    ease: settle (at each time the value sets off for its new value on the
    spring, arriving `visual` later), smooth (seg between keyframes, the
    value exactly there at each time), linear, or step (it jumps)."""
    times = [float(t) for t in times]
    if len(times) != len(values) or any(b < a for a, b in zip(times, times[1:])):
        raise ValueError("keys: one value a time, the times in order")
    kw = {"p": prop, "t": [_r(t) for t in times], "v": list(values), "e": ease}
    if ease == "settle":
        kw["vd"] = visual
    if nd is not None:
        kw["nd"] = nd
    return Spec("keys", times[0], **kw)


def after(spec, gap=0.0):
    """The moment `gap` seconds after a spec has arrived."""
    return spec.end + gap


def _each(anim, n):
    """The spec of each of n marks: one spec for all (a seq or a stagger
    gives each its own start), a list of n, or a function of the index."""
    if anim is None:
        return [None] * n
    if isinstance(anim, (Spec, Specs)):
        anim.bind(n)
        return [anim.at(i) for i in range(n)]
    if callable(anim):
        return [anim(i) for i in range(n)]
    anim = list(anim)
    if len(anim) != n:
        raise ValueError(f"anim: {len(anim)} specs for {n} marks")
    return anim


def _ajson(anim):
    return _json.dumps(anim.json(), separators=(",", ":"))


def _svg_anim(anim, ghost=False):
    """The attributes an SVG mark carries for anim.js."""
    out = ""
    if anim is not None:
        out += f" data-anim='{_ajson(anim)}'"
    if ghost:
        out += ' data-ghost="" display="none"'
    return out


def _html_anim(anim, ghost=False):
    out = ""
    if anim is not None:
        out += f" data-anim='{_ajson(anim)}'"
    if ghost:
        out += " data-ghost hidden"
    return out


def _mapkeys(anim, fn):
    """The spec with each keys' values passed through fn(prop, values)."""
    if anim is None:
        return None
    if isinstance(anim, Specs):
        return Specs(*[_mapkeys(p, fn) for p in anim.parts])
    if anim.kind != "keys":
        return anim
    kw = dict(anim.kw)
    kw["v"] = fn(kw["p"], kw["v"])
    return Spec("keys", anim.t, dt=anim.dt, times=anim.times, n=anim.n, **kw)


def _offsets(anim):
    """Keys of where a mark is (px) become how far it is from its place, the
    last keyframe: the runtime moves a mark by these. (Twice is once: the
    last is then 0.)"""
    def fn(p, v):
        if p == "xy":
            lx, ly = (float(c) for c in v[-1])
            return [[_r(float(x) - lx, 2), _r(float(y) - ly, 2)] for x, y in v]
        if p in ("x", "y"):
            return [_r(float(x) - float(v[-1]), 2) for x in v]
        if p in ("h", "p", "o", "s"):
            return [_r(x, 4) for x in v]
        return v
    return _mapkeys(anim, fn)


class C:
    """The palette: the site's tokens (site/parts/theme.py) and the figure
    palette (tools/numfig/engine.js)."""
    paper = "#FFFFFF"
    ink = "#27221C"; body = "#544F48"; muted = "#6F6A64"; guide = "#8A857C"
    rule = "#E5E1DB"; line = "#D7D2CA"; grid = "#ECE8E2"; card = "#F2EFE9"
    navy = "#043052"; blue = "#095A94"; sky = "#5B8DB8"; mist = "#A9C3DA"
    steel = "#E3EBF2"; steel2 = "#C9D7E4"
    # the crimson (tools/ROUND11.md): accent for strokes and words, amber for
    # fills, deep for dark strokes, wash for a tint behind a highlight
    accent = "#A7203A"; amber = "#D14457"; deep = "#781E2C"; wash = "#F9EEEE"
    # his orange, kept only where his words on the slide name the colour
    # (slides 30 and 37): a fill and its edge, as tools/numfig's K.orange
    orange = "#D9822B"; orange_edge = "#A5510B"


def mix(a, b, t):
    """The colour t of the way from b to a (#RRGGBB), as TikZ's a!t!b."""
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(t * x + (1 - t) * y):02X}" for x, y in zip(pa, pb))


AXIS_W = 2.0        # the box and the ticks
TICK_L = 10.0       # inward tick length
DATA_W = 4.0        # a data curve
GUIDE_W = 1.5       # a guide, dashed
GUIDE_DASH = "8 6"
GRID_W = 1.2
TICK_PX = 28        # tick labels
LABEL_PX = 30       # axis labels and annotations


def num(v, nd=None):
    """A tick number as TeX prints it: no trailing zeros, a true minus sign."""
    if nd is None:
        if abs(v - round(v)) < 1e-9:
            s = str(int(round(v)))
        else:
            s = f"{v:.6f}".rstrip("0").rstrip(".")
    else:
        s = f"{v:.{nd}f}"
    return s.replace("-", "−")


def is_num(s):
    """A tick label that is a number (data), not words."""
    import re
    plain = _html.unescape(re.sub(r"<[^>]+>", "", s))
    return bool(re.fullmatch(r"[\s0-9.,−+%×·()\-⁰¹²³⁴⁵⁶⁷⁸⁹⁻/]*", plain))


def _f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _attrs(**kw):
    out = []
    for k, v in kw.items():
        if v is None or v is False:
            continue
        out.append(f'{k.rstrip("_").replace("_", "-")}="{v}"')
    return " ".join(out)


# TikZ anchors: where on the label's box the point (x, y) sits
ANCHOR = {
    "center": (-50, -50), "north": (-50, 0), "south": (-50, -100), "east": (-100, -50),
    "west": (0, -50), "north east": (-100, 0), "north west": (0, 0),
    "south east": (-100, -100), "south west": (0, -100),
    "base": (-50, -78), "base west": (0, -78), "base east": (-100, -78),
}


def stealth(x, y, ang, w):
    """TikZ's Stealth arrow tip for a line of width w, its point at (x, y),
    pointing along angle ang (radians). Returns (path d, how far back along
    the line the stroke should stop)."""
    L, W = 6.0 * w + 4.0, 4.6 * w + 3.0
    inset = 0.32 * L
    ca, sa = math.cos(ang), math.sin(ang)

    def p(u, v):  # u along the arrow (backwards is negative), v across
        return x + u * ca - v * sa, y + u * sa + v * ca

    pts = [p(0, 0), p(-L, W / 2), p(-L + inset, 0), p(-L, -W / 2)]
    d = "M" + " L".join(f"{_f(a)} {_f(b)}" for a, b in pts) + " Z"
    return d, L - inset


def _cap(dash):
    """A dash pattern's line cap: a dotted line (dashes shorter than a pixel) is
    drawn as dots, which only a round cap makes; every other pattern keeps its
    square-cut ends."""
    if dash:
        try:
            if float(str(dash).split()[0]) < 1:
                return "round"
        except ValueError:
            pass
    return "butt"


class Fig:
    """An SVG canvas w x h in slide px, with HTML labels over it."""

    _uid = 0

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.els, self.defs, self.labels = [], [], []
        self.cues = {}
        Fig._uid += 1
        self.uid = f"f{Fig._uid}"

    # ---------------------------------------------------------- drawing
    # Each mark is kept with the clip it is drawn inside, and html() puts a
    # run of marks that share one clip in a single clipped group: the same
    # picture, but the slide's vector copies (render.py: the PDF and the SVG)
    # then set that clip once for a whole cloud of points, not once a point.
    def _el(self, markup, clip=None):
        self.els.append((markup, clip))

    def path(self, d, stroke=C.ink, width=AXIS_W, fill="none", dash=None, opacity=None,
             cap="round", join="round", clip=None, fill_opacity=None, anim=None, ghost=False):
        stroke_opacity = None
        # a mark with one paint (a stroke or a fill) takes its opacity on that
        # paint: it looks the same, and a PDF draws it with an alpha instead of
        # a transparency group of its own
        if opacity is not None and fill == "none":
            stroke_opacity, opacity = opacity, None
        elif opacity is not None and stroke == "none":
            fill_opacity = opacity * (1 if fill_opacity is None else fill_opacity)
            opacity = None
        self._el(f'<path d="{d}" {_attrs(stroke=stroke, stroke_width=_f(width) if stroke != "none" else None, fill=fill, stroke_dasharray=dash, opacity=opacity, fill_opacity=fill_opacity, stroke_opacity=stroke_opacity, stroke_linecap=cap, stroke_linejoin=join)}{_svg_anim(_offsets(anim), ghost)}/>', clip)

    def line(self, pts, **kw):
        pts = list(pts)
        if len(pts) < 2:
            return
        d = "M" + " L".join(f"{_f(x)} {_f(y)}" for x, y in pts)
        self.path(d, **kw)

    def poly(self, pts, fill, stroke="none", width=0, **kw):
        d = "M" + " L".join(f"{_f(x)} {_f(y)}" for x, y in pts) + " Z"
        self.path(d, stroke=stroke, width=width or AXIS_W, fill=fill, **kw)

    def rect(self, x, y, w, h, fill="none", stroke=None, width=AXIS_W, clip=None, anim=None,
             ghost=False, **kw):
        self._el(f'<rect {_attrs(x=_f(x), y=_f(y), width=_f(w), height=_f(h), fill=fill, stroke=stroke, stroke_width=_f(width) if stroke else None, **kw)}{_svg_anim(_offsets(anim), ghost)}/>', clip)

    def circle(self, x, y, r, fill=C.navy, stroke=None, width=2, opacity=None, clip=None, anim=None,
               ghost=False):
        """A disc, drawn as the four cubic arcs PostScript and TikZ draw a
        circle with (within 0.03 % of the radius): a PDF keeps those four,
        where a browser's own circle reaches it as sixteen."""
        k = 0.5522847498 * r
        d = (f"M{_f(x + r)} {_f(y)}C{_f(x + r)} {_f(y + k)} {_f(x + k)} {_f(y + r)} {_f(x)} {_f(y + r)}"
             f"C{_f(x - k)} {_f(y + r)} {_f(x - r)} {_f(y + k)} {_f(x - r)} {_f(y)}"
             f"C{_f(x - r)} {_f(y - k)} {_f(x - k)} {_f(y - r)} {_f(x)} {_f(y - r)}"
             f"C{_f(x + k)} {_f(y - r)} {_f(x + r)} {_f(y - k)} {_f(x + r)} {_f(y)}Z")
        fill_opacity = stroke_opacity = None
        if opacity is not None and not stroke:
            fill_opacity, opacity = opacity, None
        elif opacity is not None and fill == "none":
            stroke_opacity, opacity = opacity, None
        self._el(f'<path d="{d}" {_attrs(fill=fill, stroke=stroke, stroke_width=_f(width) if stroke else None, opacity=opacity, fill_opacity=fill_opacity, stroke_opacity=stroke_opacity)}{_svg_anim(_offsets(anim), ghost)}/>', clip)

    def arrow(self, p0, p1, color=C.ink, width=3.0, dash=None, anim=None, ghost=False):
        """A straight arrow from p0 to p1 with a Stealth tip at p1. Drawn
        (anim=draw(..)), the tip comes as the line reaches it."""
        (x0, y0), (x1, y1) = p0, p1
        ang = math.atan2(y1 - y0, x1 - x0)
        d, back = stealth(x1, y1, ang, width)
        self.line([(x0, y0), (x1 - back * math.cos(ang), y1 - back * math.sin(ang))],
                  stroke=color, width=width, dash=dash, cap="butt", anim=anim, ghost=ghost)
        self.path(d, stroke="none", fill=color, anim=anim.head() if anim is not None else None,
                  ghost=ghost)

    def count(self, value, anim, nd=0):
        """A number inside a label that counts (anim=keys(.., prop="text")):
        the <span> to put in the label's words, showing `value` as the slide
        does (nd places, a true minus sign)."""
        s = num(value, nd)
        last = anim.parts[-1] if isinstance(anim, Specs) else anim
        if last.kind == "keys" and last.kw["p"] == "text":
            assert num(float(last.kw["v"][-1]), nd) == s, "the count must end on the number the slide shows"
            last.kw["nd"] = nd
        return f"<span{_html_anim(anim)}>{s}</span>"

    def cue(self, name, t):
        """A named moment of this figure (seconds from its start): a block of
        the slide's text can start there (data-in="name" or "name+0.3")."""
        self.cues[name] = _r(t)
        return t

    def text(self, x, y, s, anchor="center", size=None, color=None, cls="", font=None,
             weight=None, rot=0, dx=0, dy=0, anim=None, ghost=False):
        """A label of his at (x, y), its `anchor` there (TikZ's names).
        `s` is HTML: his words, with <m>..</m> for his maths. `font` is None
        (Computer Modern, as every figure word), "serif" or "sans"."""
        ax, ay = ANCHOR[anchor]
        st = [f"left:{_f(x + dx)}px", f"top:{_f(y + dy)}px"]
        tf = f"translate({ax}%,{ay}%)"
        if rot:
            tf += f" rotate({rot}deg)"
        st.append(f"transform:{tf}")
        if rot:
            st.append("transform-origin:0 0" if anchor != "center" else "transform-origin:50% 50%")
        if size:
            st.append(f"font-size:{size}px")
        if color:
            st.append(f"color:{color}")
        if weight:
            st.append(f"font-weight:{weight}")
        if font == "serif":
            st.append("font-family:var(--serif)")
        elif font == "sans":
            st.append("font-family:var(--sans)")
        klass = f"ft {cls}{' ml' if '<br' in s else ''}".strip()
        self.labels.append(f'<span class="{klass}" style="{";".join(st)}"{_html_anim(_offsets(anim), ghost)}>{s}</span>')

    def clip_rect(self, x, y, w, h):
        cid = f"{self.uid}c{len(self.defs)}"
        self.defs.append(f'<clipPath id="{cid}"><rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}"/></clipPath>')
        return cid

    def axes(self, x, y, w, h, **kw):
        return Axes(self, x, y, w, h, **kw)

    def marks(self):
        """The marks in drawing order, each run that shares a clip in one
        clipped group (a slide's script may also append plain markup)."""
        out, run, at = [], [], None

        def flush():
            if run:
                out.append(f'<g clip-path="url(#{at})">{"".join(run)}</g>' if at else "".join(run))
                run.clear()
        for e in self.els:
            markup, clip = (e, None) if isinstance(e, str) else e
            if clip != at:
                flush()
                at = clip
            run.append(markup)
        flush()
        return "".join(out)

    def html(self, cls="", style=""):
        svg = (f'<svg width="{_f(self.w)}" height="{_f(self.h)}" viewBox="0 0 {_f(self.w)} {_f(self.h)}" '
               f'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
               + (f"<defs>{''.join(self.defs)}</defs>" if self.defs else "")
               + self.marks() + "</svg>")
        st = f"width:{_f(self.w)}px;height:{_f(self.h)}px;{style}"
        klass = f"fig {cls}".strip()
        return f'<div class="{klass}" style="{st}">' + svg + "".join(self.labels) + "</div>"


class Axes:
    """A pgfplots axis: the plot box at (x, y, w, h) in the figure, data
    limits xlim and ylim. frame() draws the box, ticks and labels; the data
    methods draw inside the box, clipped to it."""

    def __init__(self, fig, x, y, w, h, xlim=(0, 1), ylim=(0, 1), xlog=False, ylog=False,
                 xticks=None, yticks=None, xticklabels=None, yticklabels=None,
                 xlabel=None, ylabel=None, grid=False, box=True, ticks="both", frame=True,
                 xtick_nd=None, ytick_nd=None, ylabel_gap=None):
        self.f, self.x, self.y, self.w, self.h = fig, x, y, w, h
        self.xlim, self.ylim, self.xlog, self.ylog = xlim, ylim, xlog, ylog
        self.clip = fig.clip_rect(x, y, w, h)
        if frame:
            self.frame(xticks, yticks, xticklabels, yticklabels, xlabel, ylabel, grid, box, ticks,
                       xtick_nd, ytick_nd, ylabel_gap)

    # ---------------------------------------------------------- maps
    def X(self, v):
        a, b = self.xlim
        if self.xlog:
            v, a, b = np.log10(v), math.log10(a), math.log10(b)
        return self.x + (np.asarray(v, float) - a) / (b - a) * self.w

    def Y(self, v):
        a, b = self.ylim
        if self.ylog:
            v, a, b = np.log10(v), math.log10(a), math.log10(b)
        return self.y + self.h - (np.asarray(v, float) - a) / (b - a) * self.h

    def P(self, x, y):
        return float(self.X(x)), float(self.Y(y))

    # ---------------------------------------------------------- frame
    def frame(self, xticks=None, yticks=None, xticklabels=None, yticklabels=None, xlabel=None,
              ylabel=None, grid=False, box=True, ticks="both", xtick_nd=None, ytick_nd=None,
              ylabel_gap=None):
        f, x, y, w, h = self.f, self.x, self.y, self.w, self.h
        xt = list(xticks) if xticks is not None else []
        yt = list(yticks) if yticks is not None else []
        if grid:
            for v in xt:
                X = float(self.X(v))
                if x + 1 < X < x + w - 1:
                    f.line([(X, y), (X, y + h)], stroke=C.grid, width=GRID_W, cap="butt")
            for v in yt:
                Y = float(self.Y(v))
                if y + 1 < Y < y + h - 1:
                    f.line([(x, Y), (x + w, Y)], stroke=C.grid, width=GRID_W, cap="butt")
        # ticks: inward and mirrored on a box (pgfplots' default), or "in",
        # "out" (tick align=outside) or "none" on the bottom and left only
        both = box and ticks == "both"
        sgn = -1 if ticks == "out" else 1
        L = 0 if ticks == "none" else TICK_L
        for v in xt:
            X = float(self.X(v))
            f.line([(X, y + h), (X, y + h - sgn * L)], stroke=C.ink, width=AXIS_W, cap="butt")
            if both:
                f.line([(X, y), (X, y + L)], stroke=C.ink, width=AXIS_W, cap="butt")
        for v in yt:
            Y = float(self.Y(v))
            f.line([(x, Y), (x + sgn * L, Y)], stroke=C.ink, width=AXIS_W, cap="butt")
            if both:
                f.line([(x + w, Y), (x + w - L, Y)], stroke=C.ink, width=AXIS_W, cap="butt")
        if box:
            f.rect(x, y, w, h, stroke=C.ink, width=AXIS_W)
        else:
            f.line([(x, y), (x, y + h), (x + w, y + h)], stroke=C.ink, width=AXIS_W, cap="square",
                   join="miter")
        # the numbers (class tk: data, exempt from the words check); a tick
        # labelled with his words (a, b; class tl) is his text and is checked
        off = 14 + (L if ticks == "out" else 0)
        for i, v in enumerate(xt):
            s = xticklabels[i] if xticklabels is not None else num(v, xtick_nd)
            if s != "":
                f.text(float(self.X(v)), y + h + off, s, "north", cls="tk" if is_num(s) else "tl")
        widest = 0
        for i, v in enumerate(yt):
            s = yticklabels[i] if yticklabels is not None else num(v, ytick_nd)
            if s != "":
                f.text(x - off, float(self.Y(v)), s, "east", cls="tk" if is_num(s) else "tl")
                widest = max(widest, len(_html.unescape(s)))
        if xlabel:
            f.text(x + w / 2, y + h + off + (TICK_PX + 16 if xt else 0), xlabel, "north", cls="axl")
        if ylabel:
            gap = ylabel_gap if ylabel_gap is not None else off + widest * 0.5 * TICK_PX + 22 + LABEL_PX / 2
            f.text(x - gap, y + h / 2, ylabel, "center", cls="axl", rot=-90)

    # ---------------------------------------------------------- data
    def _pts(self, xs, ys):
        return list(zip(np.asarray(self.X(xs), float), np.asarray(self.Y(ys), float)))

    def plot(self, xs, ys, color=C.navy, width=DATA_W, dash=None, clip=True, opacity=None):
        self.f.line(self._pts(xs, ys), stroke=color, width=width, dash=dash,
                    clip=self.clip if clip else None, opacity=opacity)

    def area(self, xs, y1, y0=0.0, color=C.mist, opacity=None, clip=True):
        xs = np.asarray(xs, float)
        y1 = np.broadcast_to(np.asarray(y1, float), xs.shape)
        y0 = np.broadcast_to(np.asarray(y0, float), xs.shape)
        pts = self._pts(xs, y1) + self._pts(xs[::-1], y0[::-1])
        self.f.poly(pts, fill=color, fill_opacity=opacity, clip=self.clip if clip else None)

    def bars(self, xs, hs, width=0.7, color=C.navy, base=0.0, opacity=None, stroke=None):
        for xv, hv in zip(xs, hs):
            X0, X1 = float(self.X(xv - width / 2)), float(self.X(xv + width / 2))
            Y0, Y1 = float(self.Y(base)), float(self.Y(base + hv))
            self.f.rect(X0, min(Y0, Y1), X1 - X0, abs(Y0 - Y1), fill=color, stroke=stroke,
                        width=1.5, fill_opacity=opacity, clip=self.clip)

    def scatter(self, xs, ys, r=5.0, color=C.navy, opacity=None, stroke=None, clip=True):
        for X, Y in self._pts(xs, ys):
            self.f.circle(X, Y, r, fill=color, stroke=stroke, opacity=opacity,
                          clip=self.clip if clip else None)

    def mark(self, xv, yv, r=10.0, color=C.accent, ring=C.paper, ring_w=3.0):
        """The operating point: a filled disc with a paper ring."""
        X, Y = self.P(xv, yv)
        self.f.circle(X, Y, r + ring_w, fill=ring)
        self.f.circle(X, Y, r, fill=color)

    def hline(self, yv, color=C.guide, width=GUIDE_W, dash=GUIDE_DASH, x0=None, x1=None):
        a = self.xlim[0] if x0 is None else x0
        b = self.xlim[1] if x1 is None else x1
        self.f.line(self._pts([a, b], [yv, yv]), stroke=color, width=width, dash=dash, cap=_cap(dash),
                    clip=self.clip)

    def vline(self, xv, color=C.guide, width=GUIDE_W, dash=GUIDE_DASH, y0=None, y1=None):
        a = self.ylim[0] if y0 is None else y0
        b = self.ylim[1] if y1 is None else y1
        self.f.line(self._pts([xv, xv], [a, b]), stroke=color, width=width, dash=dash, cap=_cap(dash),
                    clip=self.clip)

    def text(self, xv, yv, s, anchor="center", **kw):
        X, Y = self.P(xv, yv)
        self.f.text(X, Y, s, anchor, **kw)

    def leader(self, p_from, p_to, color=C.accent, width=2.0, gap=0.0):
        """A thin line from a label (figure px) to a data point (data
        coordinates), stopping `gap` px short of the point."""
        (x0, y0) = p_from
        x1, y1 = self.P(*p_to)
        if gap:
            L = math.hypot(x1 - x0, y1 - y0)
            x1, y1 = x1 - (x1 - x0) * gap / L, y1 - (y1 - y0) * gap / L
        self.f.line([(x0, y0), (x1, y1)], stroke=color, width=width, cap="round")

    def legend(self, entries, at="north east", pad=16, row=38, sample=44, size=24, inset=14):
        """pgfplots' legend: a 1 px ink box, white, inside the axis. entries
        are (label HTML, dict of the line's style: color, width, dash, or
        kind='area'/'mark')."""
        f = self.f
        est_w = max(len(_html.unescape(__import__("re").sub(r"<[^>]+>", "", t))) for t, _ in entries) * size * 0.5
        bw = pad + sample + 12 + est_w + pad
        bh = pad * 2 + row * len(entries) - (row - size)
        bx = self.x + self.w - inset - bw if "east" in at else self.x + inset
        by = self.y + inset if "north" in at else self.y + self.h - inset - bh
        f.rect(bx, by, bw, bh, fill=C.paper, stroke=C.ink, width=1.0)
        for i, (t, st) in enumerate(entries):
            cy = by + pad + size / 2 + i * row
            kind = st.get("kind", "line")
            if kind == "area":
                f.rect(bx + pad, cy - 10, sample, 20, fill=st.get("color", C.mist),
                       fill_opacity=st.get("opacity"))
            elif kind == "mark":
                f.circle(bx + pad + sample / 2, cy, st.get("r", 6), fill=st.get("color", C.navy))
            else:
                f.line([(bx + pad, cy), (bx + pad + sample, cy)], stroke=st.get("color", C.navy),
                       width=st.get("width", DATA_W - 1), dash=st.get("dash"), cap=_cap(st.get("dash")))
            f.text(bx + pad + sample + 12, cy, t, "west", size=size)
        return bx, by, bw, bh


    # ---------------------------------------------------------- more marks
    def step(self, xs, ys, where="post", **kw):
        """A step function (a CDF, a counting process): level after each x."""
        xs, ys = np.asarray(xs, float), np.asarray(ys, float)
        px, py = [xs[0]], [ys[0]]
        for i in range(1, len(xs)):
            if where == "post":
                px += [xs[i], xs[i]]
                py += [ys[i - 1], ys[i]]
            else:
                px += [xs[i - 1], xs[i]]
                py += [ys[i], ys[i]]
        self.plot(px, py, **kw)

    def stem(self, xs, ys, color=C.navy, width=3.0, r=6.0, base=0.0):
        """Stems from a base line with a dot on each (autocorrelations, a
        probability mass function)."""
        for xv, yv in zip(xs, ys):
            self.f.line(self._pts([xv, xv], [base, yv]), stroke=color, width=width, cap="butt",
                        clip=self.clip)
        self.scatter(xs, ys, r=r, color=color)

    def hist(self, values, edges, density=True, color=C.steel2, stroke=None, gap=0.08):
        """A histogram of `values` on the bin `edges` (numpy's), bars touching
        but for a hairline gap. Returns the heights."""
        h, e = np.histogram(values, edges, density=density)
        w = np.diff(e)
        self.bars((e[:-1] + e[1:]) / 2, h, width=w * (1 - gap) if np.ndim(w) == 0 else float(w[0]) * (1 - gap),
                  color=color, stroke=stroke)
        return h

    def errorbar(self, xs, ys, lo, hi, color=C.navy, width=2.5, cap=8.0, r=6.0):
        """A vertical interval [lo, hi] at each x, with caps and the point."""
        for xv, yv, a, b in zip(xs, ys, lo, hi):
            X = float(self.X(xv))
            Ya, Yb = float(self.Y(a)), float(self.Y(b))
            self.f.line([(X, Ya), (X, Yb)], stroke=color, width=width, cap="butt")
            for Yc in (Ya, Yb):
                self.f.line([(X - cap, Yc), (X + cap, Yc)], stroke=color, width=width, cap="butt")
        self.scatter(xs, ys, r=r, color=color)

    def interval(self, a, b, y, color=C.navy, width=3.0, cap=12.0):
        """A horizontal interval [a, b] at height y, capped at both ends (a
        confidence interval)."""
        Xa, Xb, Y = float(self.X(a)), float(self.X(b)), float(self.Y(y))
        self.f.line([(Xa, Y), (Xb, Y)], stroke=color, width=width, cap="butt")
        for X in (Xa, Xb):
            self.f.line([(X, Y - cap), (X, Y + cap)], stroke=color, width=width, cap="butt")


# the order his series take their colours in (DECK_BRIEF.md, "Colour"): his
# navy, his orange (now the crimson accent), his purple, his teal, his red;
# guides in C.guide
SERIES = [C.navy, C.accent, C.blue, C.sky, C.deep]


def log_ticks(lo, hi):
    """Decade ticks from 10^lo to 10^hi and their labels as TeX prints them."""
    exps = list(range(lo, hi + 1))
    return [10.0 ** e for e in exps], [f"10<sup>{num(e)}</sup>" for e in exps]


# ------------------------------------------------------------------ numbers
def grid(a, b, n=801):
    return np.linspace(a, b, n)


def sample(n, dist_x, dist_y=None, rho=0.0, skip=0):
    """n points from a stated model, deterministic: a Halton sequence (bases 2
    and 3) pushed through the inverse CDFs, so the cloud is a faithful draw
    that is the same every time. With dist_y and rho, a Gaussian copula gives
    the pair correlation rho."""
    from scipy.stats import norm, qmc
    u = qmc.Halton(d=2, scramble=False).random(n + skip + 1)[skip + 1:]
    z1, z2 = norm.ppf(u[:, 0]), norm.ppf(u[:, 1])
    if dist_y is None:
        return dist_x.ppf(u[:, 0])
    z2 = rho * z1 + math.sqrt(1 - rho * rho) * z2
    return dist_x.ppf(norm.cdf(z1)), dist_y.ppf(norm.cdf(z2))
