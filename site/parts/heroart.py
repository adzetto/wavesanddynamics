# -*- coding: utf-8 -*-
"""heroart: the home page illustration, drawn by hand in SVG.

The picture is the reference JPEG redrawn in paths
(reference/design-mockup/hero-illustration-2026-09-24.jpeg, 1300 x 940). Every
coordinate is in that image's pixel space, so any number can be checked against
the JPEG with a ruler; the figure shows the crop VB of it.

The motion is one loop of 12 seconds that tells cause and effect three times,
left to right, and ends on the frame it began with:

  A  0.4 s   the acoustic source at the tall building's foot rings and sets the
             building swaying; its sensor fires, a packet climbs to the
             regression, a new point drops into the band and the fit tips and
             settles. The spectrum answers at 3.55.
  B  2.75 s  the train leaves behind the masonry building and the next one comes
             out from behind the mid-rise block; the bridge's main span swells
             under them, a wave runs along the hangers as it brakes, the tower
             sensor fires, a packet climbs to the network, which fires layer by
             layer. The spectrum answers at 7.55.
  C  5.9 s   the car drives off at the picture's edge and comes back to park; its
             engine is heard, the message hops car, chimney, airplane and flies
             to the decision tree, whose path lights root, branch, leaf. The leaf
             turns amber: the one warm mark, the insight. The answer: 11.55.

Around it: the tall building and the bridge never quite stop vibrating, the
rotor turns, smoke rises, the airplane glides with its wings flexing, the
trace scrolls into the ripple and the bars breathe with what arrives. A model
holds its last answer until new data comes, so the picture at rest (no
script, reduced motion, print) is the loop's first and last frame. The loop
runs for as long as the figure is on screen in a visible tab: nothing a
reader does stops it (the developer's rule since 26 Sep 2026, when the pause
button went), and only the reader's own setting for reduced motion keeps it
still.

How it moves, and what the main thread does between frames. A CSS
transform animation on an element inside an SVG is handed to the compositor
only when the page can promise what it cannot: never on a screen whose zoom is
not 1 (crbug.com/1186312), never on an element a <use> repeats, and even at
zoom 1 the full home page settled, on about one load in three, into a state
where the compositor asked the main thread for a frame at every vsync
(measured in Chromium 145: 60 style recalculations and layouts a second with
a single rotating <g> on the page; a rotating <div> in its place, or an
opacity animation on the same <g>, never did). So nothing inside the drawing
moves by a CSS transform. The drawing is one SVG whose CSS animations are
opacity only (the hanger wave, the network, the links that let go of a
vehicle); what moves in it moves by SMIL, which the main thread runs and
repaints in every frame while the figure runs ("the vibration" below
measures it). Two structures vibrate in place, the tall building and the
bridge's main span. Three parts travel behind something, each inside a clip
of the drawing: the train between the two buildings, the car out to the
picture's edge and the trace up to the ripple. Those three were HTML layers
in windows with overflow hidden until 26 Sep 2026, when Safari on the
professor's iPhone drew none of them, though it drew every layer that had
no window. In the drawing they need no window, and the train and the car
are reflected by the same <use> as the city.

Every other part that moves is its own small HTML layer over the drawing: a
<span> placed in percent of the figure, holding an SVG of just that part in
the drawing's own units. The span is what the animation moves, with
translations in percent of its own box, so the motion keeps its size at any
width. No such layer is clipped by a box of its own; the figure clips them
all at its edge, paper-coloured gradients laid over the trace's ends and
the road's fade what must fade, and no mask or filter lies over anything
that moves. Nothing moves until the script has seen the figure; everything
pauses off screen and in a hidden tab. The script keeps no
IntersectionObserver (one that holds a target costs a main-thread frame at
every vsync while anything on the page animates): it looks at the figure on
scroll and resize, once a frame at most.

Thirteen buttons lie over the drawing (the ten structures and the three
models) as one toolbar: pointing at one, focusing it or pressing it keeps its
sensors, the path its data takes and the model it feeds, brightens that path
and lets the rest step back; pointing at a model traces every structure that
feeds it. One quiet line under the drawing names the pair while one is lit.
Colours are theme.py tokens: the column's navy for structure, --link for data,
--link let into --page for the tints, --accent once.
"""

import math

__all__ = ["CSS", "JS", "render"]

T = 12.0            # the story loop, seconds
LEAD = 0.6          # the story starts this long after the figure is first seen
# Every animation on the story's clock starts at once, the moment the story
# starts, each with a negative delay (t - T): at that moment it stands at its
# own place in the loop's last frame, which is the first, and reaches its
# event t seconds later. Started together they cost one frame. Three run on
# past the loop's end on purpose (the spectrum's and the ripple's last answer,
# and the insight's ring, settle in full after 12 s): at the story's start
# they would be caught in that tail, so they keep a positive delay and wait
# for their first event at rest (_at_s(cross=True)).
G = 555             # the ground line
VB = (20, 66, 1260, 812)   # the crop of the JPEG the figure shows
SHIFT = 640         # the train that arrives runs this far behind the one that leaves
CAR_GO = 330        # how far the car drives to leave the picture


def _n(v):
    """A number as SVG wants it: one decimal at most, no trailing zeros."""
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _p(v):
    """A percentage, three decimals at most: a thousandth of a percent of the
    figure is a hundredth of a pixel at any width it is drawn."""
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _grp(keys, inner, cls="", extra=""):
    """A group that steps back while another key is lit. keys: the lit keys
    that keep it (a structure, the structures its data serves, the model)."""
    k = f' data-k="{keys}"' if keys else ""
    return f'<g class="hdim{" " + cls if cls else ""}"{k}{extra}>{inner}</g>'


# ---------------------------------------------------------------- the layers
# A part that moves is an HTML layer over the drawing (see the docstring): an
# outer span placed in percent of the figure, which steps back when another
# key is lit; in it the mover, the span the animation moves; in that an SVG
# of just the part, in the drawing's own units. A box is (x, y, w, h) in
# those units.

def _q(units):
    """A length of the drawing in cqw: the figure is a size container, a
    hundredth of its width is 12.6 units."""
    return _p(units / VB[2] * 100) + "cqw"


def _box(box, frame=VB):
    """A box placed in a frame (the figure, or the mover it rides on), in
    cqw. Every length is its own fraction of the figure's width, never a
    percent of a small box, which would multiply that box's rounding to 1/64
    px (a layer the size of a ring, told to draw an SVG 50 times its size,
    drew it a third of a pixel off the drawing under it)."""
    x, y, w, h = box
    fx, fy = frame[0], frame[1]
    return f"left:{_q(x - fx)};top:{_q(y - fy)};width:{_q(w)};height:{_q(h)}"


def _svg(box, inner):
    """An SVG of one part, in the element whose box is box. The SVG itself
    covers the whole figure, with the drawing's own viewBox: Chrome snaps an
    SVG's box to whole pixels, and a box the size of the part would be snapped
    on its own (a ring drawn 7% large, a bar half a pixel off the axis); the
    size of the figure it is snapped exactly as the drawing under it is. Its
    size is the stylesheet's (the figure's, in cqw); only its place is its
    own."""
    vx, vy, vw, vh = VB
    return f'<svg viewBox="{vx} {vy} {vw} {vh}" style="{_box(VB, box).split(";width")[0]}">{inner}</svg>'


def _mover(cls, box, inner, frame=None, style="", after="", under=""):
    """The span an animation moves. It fills its layer, or sits by its own box
    in a frame (the mover it rides on). under: layers drawn below its SVG
    (the fit's band, the airplane's wings); after: layers that ride on it (a
    sensor's pulse, a wing's outer panel)."""
    st = ";".join(s for s in ((_box(box, frame) if frame else ""), style) if s)
    s = f' style="{st}"' if st else ""
    return f'<span class="ha__m {cls}"{s}>{under}{_svg(box, inner)}{after}</span>'


def _layer(box, body, keys=None, dim=True, frame=VB, cls=""):
    c = "ha__o" + (" hdim" if dim else "") + (" " + cls if cls else "")
    k = f' data-k="{keys}"' if keys and dim else ""
    return f'<span class="{c}"{k} style="{_box(box, frame)}">{body}</span>'


def _still(box, inner, keys=None, dim=True):
    """A layer that does not move: part of the drawing that must lie over a
    layer that does (the ripple's rings over the trace, the scatter's points
    over the fit that tips)."""
    return _layer(box, _svg(box, inner), keys, dim)


def _moving(cls, box, inner, keys=None, style="", after="", dim=True, under="", frame=VB):
    return _layer(box, _mover(cls, box, inner, None, style, after, under), keys, dim, frame)


def _fade(box, css):
    """Paper laid over an edge where something travels out of sight (the
    trace's two ends, the road's): a gradient of --page, still."""
    return f'<span class="ha__o" style="{_box(box)};background:{css}"></span>'


# ------------------------------------------------------------------ the city

SENSORS = {          # name: (x, y)
    "b1": (116, 413), "b2": (218, 308), "b3": (312, 378),
    "tl": (481, 326), "tr": (711.5, 326), "tn": (542, 517),
    "hub": (842, 352), "rb": (948, 397), "car": (1030, 516),
    "ch": (1090, 366), "pl": (1066, 231),
}
# the keys that keep each sensor lit: its structure, every structure whose
# data passes through it, and the model it feeds
SENSOR_KEYS = {
    "b1": "low reg", "b2": "low tall reg", "b3": "mid nn",
    "tl": "bridge train nn", "tr": "bridge nn", "tn": "train nn",
    "hub": "turbine tree", "rb": "turbine masonry tree", "car": "car tree",
    "ch": "car chimney tree", "pl": "turbine masonry car chimney plane tree",
}


def _bldg(x0, x1, top, r=5, base=G):
    return (f"M{_n(x0)} {_n(base)}V{_n(top + r)}Q{_n(x0)} {_n(top)} {_n(x0 + r)} {_n(top)}"
            f"H{_n(x1 - r)}Q{_n(x1)} {_n(top)} {_n(x1)} {_n(top + r)}V{_n(base)}Z")


def _rects(xs, ys, w, h, r):
    """Many rounded rectangles as one path (windows)."""
    out = []
    for y in ys:
        for x in xs:
            out.append(f"M{_n(x + r)} {_n(y)}h{_n(w - 2 * r)}a{_n(r)} {_n(r)} 0 0 1 {_n(r)} {_n(r)}"
                       f"v{_n(h - 2 * r)}a{_n(r)} {_n(r)} 0 0 1 -{_n(r)} {_n(r)}h-{_n(w - 2 * r)}"
                       f"a{_n(r)} {_n(r)} 0 0 1 -{_n(r)} -{_n(r)}v-{_n(h - 2 * r)}"
                       f"a{_n(r)} {_n(r)} 0 0 1 {_n(r)} -{_n(r)}z")
    return "".join(out)


def _b1():
    return (f'<path fill="url(#ha-gb1)" d="{_bldg(73, 160, 413)}"/>'
            f'<path class="hf-w" d="{_rects((85.5, 108, 130.5), (434, 460.5, 487, 513.5), 18, 11.5, 2)}"/>')


def _b2():
    """The tall building in two blocks, so that it can bend (see _lean): the
    lower from the ground to its middle, the upper from its middle to the roof,
    reaching 1 unit down over the lower so that no seam shows between them.
    Its gradient lies in user space, so the two blocks share one."""
    ys = [322 + 31.6 * i for i in range(7)]
    lower = (f'<path fill="url(#ha-gb2)" d="M176 {G}V{_n(MID)}H259V{G}Z"/>'
             f'<path class="hf-w" d="{_rects((187,), ys[4:], 61, 8.6, 4.3)}"/>')
    upper = (f'<path fill="url(#ha-gb2)" d="{_bldg(176, 259, 308, 6, MID + 1)}"/>'
             f'<path class="hf-w" d="{_rects((187,), ys[:4], 61, 8.6, 4.3)}"/>')
    return _lean(lower, upper)


def _b3():
    return (f'<path class="hf-t2" d="{_bldg(277, 346, 378)}"/>'
            f'<path class="hf-w" d="{_rects((285,), (397, 431, 465, 499), 53, 3.6, 1.8)}"/>')


def _towers():
    def tower(x):
        return (f"M{x} {G}V325.5Q{x} 324 {x + 1.5} 324H{x + 6.5}Q{x + 8} 324 {x + 8} 325.5V{G}Z"
                f"M{x + 22} {G}V325.5Q{x + 22} 324 {x + 23.5} 324H{x + 28.5}Q{x + 30} 324 "
                f"{x + 30} 325.5V{G}Z"
                f"M{x + 8} 351h14v6h-14zM{x + 8} 449h14v6h-14z")
    return f'<path class="hf-i" d="{tower(466)}{tower(697)}"/>'


def _side_y(x):
    """The side-span cables, as the reference draws them: a shoulder that leaves
    the tower top and falls to just above the deck's end (y = 329 + 0.0203 u^2,
    u the distance from the tower's axis). Mirrored on the right."""
    if x > 596:
        x = 1192 - x
    return 329 + 0.0203 * (480.5 - x) ** 2


HANGERS = [596 + 15.4 * k for k in range(-12, 13) if abs(k) <= 6 or abs(k) >= 9]


# ------------------------------------------------------------- the vibration
# The tall building and the bridge's main span vibrate as structures do. The
# professor asked for it on 25 Sep 2026, "at least like before": in round 4's
# draft b a gust rocked the building (1.1 degrees, a period of 0.8 s, gone in
# 1.9 s) and the deck rang as the train arrived (a period of 0.6 s, gone in
# 1.5 s), once a loop, and the merge dropped both as too slight to see. Here
# each moves at its own natural period and is never quite still: a light
# ambient motion that swells and eases, and a response to the story that
# grows at once and dies away over seconds. The acoustic source at the
# building's foot (0.42 s) sets it ringing, so its sensor fires as the roof
# swings through the middle and the largest swing comes at 1.125 s; the span
# swells while the trains pass under it and swings most as they stop
# (5.25 s), as the tower sensor fires.
#
# The motion is SMIL on the drawing's own clock: <animateTransform> leans the
# building, <animate> bends the span's cable and deck. A bend needs `d`, which
# CSS animates in Chromium and Firefox but not in WebKit, where SMIL does it;
# and SMIL values reach the reflection's <use> clones, where Chrome runs no
# CSS animation, so the reflection moves with its structure. Each animation
# is one loop of the story that starts and ends at rest, so the picture at
# rest is still its first and last frame; the script begins them with the
# story, pauses them with it and holds them at rest when it must. The
# envelope is sampled at each extreme and joined by half a cosine (by a
# quarter from rest and back to it), so every swing is as large as the
# envelope says and no velocity ever jumps.
#
# What it costs, measured in Chromium at 60 Hz (the home page at 1280 x 800,
# the median of four runs): 3.0 ms of main thread a frame, against 1.4 ms with
# the two structures still and 2.8 ms for the CSS `d` and skewX it replaced.
# Whatever moves inside the drawing has it repainted and the page's layers
# rebuilt in every frame. Drawing the lean and the hangers with `d` alone,
# which spares the rebuild, measured 2.4 to 2.7 ms: too little gained for the
# 1 KB more markup it takes.
# The travellers moved onto the same clock on 26 Sep 2026 for 0.2 ms more:
# 4.1 ms against 3.9 ms with their five translations taken out, headless
# Chromium, the median of five runs taken in turn.

SWAY_P = 1.5        # the tall building's natural period, seconds: 8 cycles a loop
SPAN_P = 1.0        # the main span's: 12 cycles a loop
MID = 431.5         # the tall building's mid-height, where its upper half bends
UPPER = 0.5         # the upper half's own lean, as a share of the whole's: the
#                     middle then moves 0.4 of the roof, as in a first mode, and
#                     in step with it, as every floor does in a mode (until 27 Sep
#                     2026 the roof led the middle by 0.2 s, a travelling look
#                     that no mode of a building fixed at its foot has)
ROOF = G - 308 + UPPER * (MID - 308)    # the roof's travel for a whole's tangent of 1
# keySplines: half a cosine between two extremes (to 1.2% of a swing; .37 0
# .63 1 comes closer, but this one is written 129 times), and a quarter sine
# from rest to an extreme and back
SINE_INOUT, SINE_OUT, SINE_IN = ".4 0 .6 1", ".61 1 .88 1", ".12 0 .39 0"


def _sway_env(t):
    """The tall building's sway at its roof, units, at the swing near t: a
    breeze (2.6) with one gust at 9.3 s, and from 0.42 s the ring the acoustic
    source at its foot sets off, 5.4 more at the next swing (1.125 s), dying
    away with a time constant of 1.9 s."""
    breeze = 2.6 + 0.9 * math.exp(-((t - 9.3) / 1.4) ** 2)
    return breeze + (5.4 * math.exp(-(t - 1.125) / 1.9) if t > 0.42 else 0.0)


def _span_env(t):
    """The main span's bend at midspan, units, at the swing near t: 2.5 that
    wanders slowly, then the trains that pass under it from 2.75 s building it
    up by 5.5 until 5.25 s, and its ring-down after (time constant 1.6 s)."""
    amb = 2.5 + 0.4 * math.sin(math.pi * t / 3 + 0.5)
    if t < 2.75:
        return amb
    if t <= 5.25:
        u = (t - 2.75) / 2.5
        return amb + 5.5 * u * u * (3 - 2 * u)
    return amb + 5.5 * math.exp(-(t - 5.25) / 1.6)


def _swings(period, env):
    """One loop of a vibration as (time, value, spline to the next): at rest
    at 0 and at T, and between them an extreme every half period, alternating
    in sign, as large as env says for that swing."""
    n = round(2 * T / period)
    stops = [(0.0, 0.0, SINE_OUT)]
    for k in range(n):
        t = period / 4 + k * period / 2
        stops.append((t, (-1) ** k * env(t), SINE_INOUT if k < n - 1 else SINE_IN))
    return stops + [(T, 0.0, None)]


def _dec(v, d):
    """A number with d decimals at most: no trailing zeros, no leading zero
    (".5"), which SMIL's lists read as well and which keeps them short."""
    s = f"{v:.{d}f}".rstrip("0").rstrip(".")
    s = "-" + s[2:] if s.startswith("-0.") else s[1:] if s.startswith("0.") else s
    return "0" if s in ("", "-0") else s


def _smil(stops, fmt, kind="d", master=False):
    """One loop of the story as a SMIL animation of its parent element, which
    repeats on the drawing's clock once begun. The master (one, outside
    anything a <use> repeats) is begun by the script with the story; every
    other begins with it, by name, which is also how the copies inside the
    reflection's clones begin in Firefox (a script cannot reach those). Its
    id breaks the ha- rule: in a SMIL time reference a hyphen reads as an
    offset ("ha - vib.begin"), and the escape SMIL defines for it works in
    Firefox only. What it animates it adds to what the parent has: kind
    "skewX", a lean in degrees after its transform; "translate", a move
    along x (a vehicle, the trace); "d", a bend added to its d (see
    _bend)."""
    what = {"d": 'animate attributeName="d"',
            "skewX": 'animateTransform attributeName="transform" type="skewX"',
            "translate": 'animateTransform attributeName="transform" type="translate"'}[kind]
    begin = 'id="ha_vib" begin="indefinite"' if master else 'begin="ha_vib.begin"'
    return (f'<{what} additive="sum" {begin} dur="{T:g}s" repeatDur="indefinite" calcMode="spline" '
            f'keyTimes="{";".join(_dec(t / T, 3) for t, _, _ in stops)}" '
            f'keySplines="{";".join(s for _, _, s in stops[:-1])}" '
            f'values="{";".join(fmt(v) for _, v, _ in stops)}"/>')


def _lean(lower, upper):
    """What leans with the tall building: the whole of it leans from the ground
    and its upper half a little more, in step, from its middle.
    skewX moves a point by its height over the pivot times the tangent, so the
    roof travels ROOF times the whole's tangent; a sway of d units at the roof
    is a whole's tangent of d / ROOF. Positive d leans it to the right."""
    def deg(share):
        return lambda d: _dec(-math.degrees(math.atan(share * d / ROOF)), 2)
    whole = _smil(_swings(SWAY_P, _sway_env), deg(1), "skewX")
    top = _smil(_swings(SWAY_P, _sway_env), deg(UPPER), "skewX")
    return (f'<g transform="translate(0 {G})">{whole}<g transform="translate(0 -{G})">{lower}'
            f'<g transform="translate(0 {_n(MID)})">{top}<g transform="translate(0 -{_n(MID)})">'
            f'{upper}</g></g></g></g>')


# The main span bends in its first mode, as a parabola across it (within 5%
# of a half sine, and the shape the cable's own sag already has): the cable,
# the deck's centre line and the room between them are each one quadratic,
# written relative to the tower, whose control point drops 2a for a bend of a
# at midspan. The animation adds only that drop to the path at rest, which
# keeps its lists short. The main span's hangers run long and show only
# through that room (a clip), so they follow the cable and the deck, and so
# does the hanger wave, which is clipped the same way. The towers and the
# side spans hold.
CABLE = "M496 343q100 105 200 0"
SPAN = "M496 482.25q100 0 200 0"         # the deck's centre line, stroked 8.5 wide
GAP = "M496 344.6q100 105 200 0V482q-100 0 -200 0Z"   # from under the cable into the deck


def _bend(a, gap=False):
    """What a bend of a adds to CABLE or SPAN, or to GAP, whose two sides both
    bend."""
    d = _n(2 * a)
    return f"M0 0q0 {d} 0 0V0q0 {d} 0 0Z" if gap else f"M0 0q0 {d} 0 0"


def _span_smil(gap=False):
    return _smil(_swings(SPAN_P, _span_env), lambda a: _bend(a, gap), master=gap)


def _hangers(xs):
    """Hangers at xs: on a side span from its cable to the deck; on the main
    span long enough to fill the room at any bend (see GAP)."""
    return "".join(f"M{_n(x)} 335V492" if 496 < x < 696 else
                   f"M{_n(x)} {_n(_side_y(x) + 1.6)}V478" for x in xs)


def _deck():
    """Deck, cables and hangers. The hangers keep one screen width at any size.
    The side spans' deck is two rounded ends that the main span's reaches
    over, so no seam shows where it bends."""
    hang = 'class="hs-h hf-n hns" stroke-width=".6"'
    main = [x for x in HANGERS if 496 < x < 696]
    return (f'<path {hang} d="{_hangers([x for x in HANGERS if x not in main])}"/>'
            f'<path {hang} clip-path="url(#ha-cgap)" d="{_hangers(main)}"/>'
            '<path class="hs-i hf-n" stroke-width="3.2" stroke-linecap="round" '
            'd="M466 333.3Q435 351.5 404 447.8M726 333.3Q757 351.5 788 447.8"/>'
            f'<path class="hs-i hf-n" stroke-width="3.2" stroke-linecap="round" d="{CABLE}">'
            f'{_span_smil()}</path>'
            '<rect class="hf-i" x="402" y="478" width="96" height="8.5" rx="1.5"/>'
            '<rect class="hf-i" x="694" y="478" width="96" height="8.5" rx="1.5"/>'
            f'<path class="hs-i hf-n" stroke-width="8.5" d="{SPAN}">{_span_smil()}</path>')


# The wave the arriving train sends along the hangers: the hangers again in
# navy, in five groups lit left to right as it brakes (opacity only).
WAVE_GROUPS = ((0, 4), (4, 8), (8, 13), (13, 17), (17, 21))


def _wave():
    out = []
    for a, b in WAVE_GROUPS:
        xs = HANGERS[a:b]
        t = 4.2 + (sum(xs) / len(xs) - 411) / 370 * 0.9
        clip = ' clip-path="url(#ha-cgap)"' if 496 < xs[0] < 696 else ""
        out.append(f'<path class="hwv"{clip} style="--d:{t - T:.2f}s" d="{_hangers(xs)}"/>')
    return "".join(out)


def _train():
    """Three cars and the locomotive at rest, and the next train SHIFT behind."""
    cars = []
    for x0 in (356, 470, 584):
        cars.append(f"M{x0} 553V524a6 6 0 0 1 6-6h94a6 6 0 0 1 6 6v29z")
    wins = _rects([x0 + dx for x0 in (356, 470, 584) for dx in (16, 37.3, 58.6, 79.9)],
                  (526,), 13, 10, 2.5)
    wheels = "".join(f'<ellipse cx="{_n(x0 + dx)}" cy="555" rx="3.6" ry="2.6"/>'
                     for x0 in (356, 470, 584) for dx in (25, 81))
    return (f'<g id="ha-tr0"><path class="hf-t" d="{"".join(cars)}"/><path class="hf-w" d="{wins}"/>'
            f'<g class="hf-i">{wheels}<path d="M698 555V520a2 2 0 0 1 2-2h57A55 37 0 0 1 812 555z"/></g>'
            '<rect class="hf-s" x="710" y="526" width="40" height="10" rx="2"/>'
            '<path class="hf-w" d="M760 526.1A45 29 0 0 1 799.8 546H760z"/></g>'
            f'<use href="#ha-tr0" x="-{SHIFT}"/>')


def _rail():
    return ('<path class="hs-h hf-n" stroke-width="3.6" stroke-dasharray="9 5.4" d="M306 565.5H909"/>'
            '<path class="hf-n" stroke="url(#ha-grail)" stroke-width="2.6" d="M300 560.5H915"/>')


# ------------------------------------------------------------ the travellers
# The train, the car and the trace travel inside the drawing, by SMIL on the
# vibration's clock (the docstring says why they are no longer HTML layers),
# each inside a clip where it must pass out of sight. A move is one loop of
# the story as (time, x, keySpline to the next), in the drawing's units and
# in story time from 0 to T, so it keeps step with the CSS animations around
# it (the links that let go of a vehicle, the ripple the trace runs into).
# The script begins, pauses and rests them with the vibration.
LINEAR = "0 0 1 1"
ACCEL = ".33 0 .67 .33"     # exactly t squared: pulling away from rest
DECEL = ".33 .67 .67 1"     # exactly 1-(1-t) squared: braking to rest
SETTLE = ".33 1 .68 1"      # 1-(1-t) cubed: braking that eases off as it stops
TRAIN_T, CAR_T = 2.75, 5.9  # when the train pulls away, when the car drives off
TRAIN_CLIP = (346, 494, 562, 70)    # between the two buildings' inner edges
TAPE_CLIP = (20, 788, 661, 64)      # up to the ripple's centre


def _train_moves():
    """Pull away (t squared), run, brake (1-(1-t) squared), one velocity
    throughout; the pair of trains moves as one. The loop ends a whole train
    on (SHIFT), which looks as it began: the train that arrived stands where
    the one that left stood, so the next loop starts from it unseen."""
    d1, d2, d3 = 190, 240, SHIFT - 430
    v = (2 * d1 + d2 + 2 * d3) / 2.4
    t1, t2 = 2 * d1 / v, 2 * d1 / v + d2 / v
    s = TRAIN_T
    return [(0, 0, LINEAR), (s, 0, ACCEL), (s + t1, d1, LINEAR), (s + t2, d1 + d2, DECEL),
            (s + 2.4, SHIFT, LINEAR), (T, SHIFT, None)]


def _car_moves():
    """The car drives off at the picture's edge (t squared), is out of sight
    for a quarter of a second and comes back to park, braking less as it
    stops (1-(1-t) cubed), so it settles instead of halting."""
    s = CAR_T
    return [(0, 0, LINEAR), (s, 0, ACCEL), (s + 1.3, CAR_GO, LINEAR), (s + 1.55, CAR_GO, SETTLE),
            (s + 2.8, 0, LINEAR), (T, 0, None)]


def _travel(moves, inner, clip=""):
    """inner, moved along x by moves, inside the clip whose id is clip."""
    g = f'<g>{_smil(moves, lambda x: _dec(x, 2), "translate")}{inner}</g>'
    return f'<g clip-path="url(#{clip})">{g}</g>' if clip else g


def _mast():
    return '<path class="hf-m" d="M839.4 356H844.6L847.4 555H836.6Z"/>'


def _blades():
    blade = "M4 -3.6L112 -0.8Q115.5 0 112 0.8L22 5.6Q6 5.8 4 3.6Z"
    blades = "".join(f'<path transform="rotate({a})" d="{blade}"/>' for a in (-123, -3, 117))
    return f'<g class="hf-s" transform="translate(842 352)">{blades}</g>'


def _masonry():
    return (f'<path fill="url(#ha-grb)" d="{_bldg(908, 988, 397)}"/>'
            f'<path class="hf-w" d="{_rects((921.5, 941, 960.5), (418, 449, 480, 511), 15, 13, 2)}"/>')


def _chimney():
    return ('<path class="hf-p" d="M1046 555V517Q1046 513 1050 513H1131Q1135 513 1135 517V555Z"/>'
            '<path class="hf-t2" d="M1083 372H1097L1097.7 401H1082.3ZM1082.1 407H1097.9L1100.2 513H1079.8Z"/>')


def _car():
    """The car, the same both ways about its middle (x 1029.5): it leaves
    to the right and comes back from the right, and a car with a front
    would reverse one of the two ways (until 27 Sep 2026 its cabin sat 5
    units back and its pillar leaned, so it reversed out of the picture)."""
    cabin = "M985 535C995 522.5 1012.5 519 1029.5 519C1046.5 519 1064 522.5 1074 535"
    return ('<path class="hf-i" d="M962 555V550C962 540.5 970.5 534.5 983.5 534.5H1075.5'
            'C1088.5 534.5 1097 540.5 1097 550V555Z"/>'
            f'<path class="hf-w" d="{cabin}Z"/>'
            f'<path class="hs-i hf-n" stroke-width="2.6" stroke-linecap="round" d="{cabin}M1029.5 520V534.5"/>'
            '<g class="hf-w hs-i" stroke-width="3"><circle cx="992" cy="553" r="9.2"/>'
            '<circle cx="1067" cy="553" r="9.2"/></g>')


PLANE = (1066, 231, -24.3)   # the airplane's own frame: its sensor, its heading


def _in_plane(inner):
    return f'<g transform="translate({PLANE[0]} {PLANE[1]}) rotate({PLANE[2]})">{inner}</g>'


# The airplane is seen from the ground, from below: its planform, so its two
# tailplanes show as its two wings do. The reference drew the far tailplane
# only, and on 27 Sep 2026 the professor saw the airplane lacked a wing
# underneath: the near one is the far one mirrored about the fuselage, in the
# near wing's paint. The fuselage's tail is rounded alike on both sides, as a
# planform's is.
TAILS = (("hf-m", "M-46 -5L-74 -30Q-78.5 -32.5 -81 -28L-63 -5Z"),
         ("hf-s", "M-46 5L-74 30Q-78.5 32.5 -81 28L-63 5Z"))


def _plane():
    """The two tailplanes, the fuselage and its window; the wings are layers
    under it (_wings), so that they can flex."""
    return _in_plane("".join(f'<path class="{c}" d="{d}"/>' for c, d in TAILS)
                     + '<path class="hf-i" d="M-67 -5.2H71C81 -5.2 89 -3.2 89 0C89 3.2 81 5.2 71 5.2H-67'
                     'Q-71 5.2 -71 1.2V-1.2Q-71 -5.2 -67 -5.2Z"/><circle class="hf-w" cx="66" cy="-.8" r="2.4"/>')


# ------------------------------------------------------------------ the wings
# The professor asked on 26 Sep 2026 whether the airplane's wing could move
# too. The wings bend as a wing does in the air, up and down, together: the
# symmetric first bending mode that turbulence excites. The root holds at the
# fuselage and the tip moves most; seen from the ground, the world's up is the
# picture's up, so a wing's every station moves up and down the picture by
# its share of the tip's travel. The far wing, which points left, turns with
# it; the near one, which points down, shortens and lengthens, as it would to
# a reader watching from below. (Until 27 Sep 2026 each wing turned in the
# plane of its planform, mirrored about the fuselage: fore and aft, which is
# not how a wing bends.)
#
# A wing is two panels cut across halfway out, each its own HTML layer on the
# airplane's mover, sheared by a CSS transform the compositor runs alone: a
# point moves up the picture by a slope times its distance out along the span
# (skewY and scaleY, about the root for the inner panel and about the cut for
# the outer, which rides on the inner). The slopes put the cut on a
# cantilever's first mode (0.31 of the tip's travel at 0.48 of the span) and
# the tip exactly where the envelope says, so the wing curves as it bends.
# The outer overlaps the inner by a unit and their fill is opaque, so no seam
# shows, and the root reaches under the fuselage to its axis, so no gap opens
# there. A wing is (root leading, tip leading, tip's control, tip trailing,
# root trailing) in the airplane's frame: the near one below the fuselage,
# the far one above it.
NEAR = ((23, 5), (-30, 47.5), (-34.5, 50), (-38.5, 44), (-8, 3))
FAR = ((26, -5), (-25, -45.5), (-30.5, -48.5), (-36.5, -42.5), (-10, -5))
WING_P = 1.2        # the wings' period, seconds: 10 cycles a loop
WING_CUT = 25       # where a wing is cut, units out from the fuselage's axis


def _mode(xi):
    """A uniform cantilever's first bending mode at xi of its span, as a
    share of its tip's travel (0.34 at half span)."""
    b = 1.8751040687
    s = (math.sinh(b) - math.sin(b)) / (math.cosh(b) + math.cos(b))

    def phi(x):
        return math.cosh(b * x) - math.cos(b * x) - s * (math.sinh(b * x) - math.sin(b * x))
    return phi(xi) / phi(1)


def _wing_env(t):
    """The wing tips' swing, units up or down the picture, at the swing near
    t: between 4.6 and 8.5 (a fifth of the span at the most), swelling twice
    a loop and most as the airplane's sensor fires. A unit is 0.27 px at a
    phone's width and 0.39 at a desktop's, so the tips swing 1.3 to 2.3 px
    on a phone and up to 3.3 px on a desktop."""
    u = 2 * math.pi * (t - FIRE["pl"])
    return 6 + 1.25 * math.cos(u / 6) + 1.25 * math.cos(u / 12)


def _to_fig(p):
    """A point of the airplane's frame in the drawing's."""
    a = math.radians(PLANE[2])
    return (PLANE[0] + p[0] * math.cos(a) - p[1] * math.sin(a),
            PLANE[1] + p[0] * math.sin(a) + p[1] * math.cos(a))


def _wing(wing):
    """A wing's inner and outer panel (paths in the airplane's frame), its
    root and its cut (the pivots, in the drawing's frame), the unit vector
    out along its span in the drawing (the airplane's own sideways axis),
    and how far out from the root its cut and its tip are."""
    ra, ta, c, tb, rb = wing
    s = 1 if ta[1] > 0 else -1

    def across(p, q, y):
        return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1]), y

    def pts(*ps):
        return "L".join(f"{_n(x)} {_n(y)}" for x, y in ps)
    a0, b0 = across(ra, ta, -s), across(rb, tb, -s)
    a1, b1 = across(ra, ta, s * WING_CUT), across(rb, tb, s * WING_CUT)
    a2, b2 = across(ra, ta, s * (WING_CUT + 1)), across(rb, tb, s * (WING_CUT + 1))
    inner = f"M{pts(b0, a0, a2, b2)}Z"
    outer = f"M{pts(a1, ta)}Q{_n(c[0])} {_n(c[1])} {_n(tb[0])} {_n(tb[1])}L{pts(b1)}Z"
    root = ((ra[0] + rb[0]) / 2, (ra[1] + rb[1]) / 2)
    cut = ((a1[0] + b1[0]) / 2, s * WING_CUT)
    tip = tuple(ta[i] / 4 + c[i] / 2 + tb[i] / 4 for i in (0, 1))
    h = math.radians(PLANE[2])
    out = (-s * math.sin(h), s * math.cos(h))
    return (inner, outer, _to_fig(root), _to_fig(cut), out,
            abs(cut[1] - root[1]), abs(tip[1] - root[1]))


WINGS = (("mwn", NEAR, "hf-s"), ("mwf", FAR, "hf-m"))   # mover, wing, paint


def _wings():
    """Each wing's inner panel, a layer on the airplane's mover, with its
    outer panel riding on it. Every box is the airplane's: only the pivots
    differ (_pivots)."""
    out = []
    for cls, wing, paint in WINGS:
        inner, outer = _wing(wing)[:2]
        tip = _moving(cls + "o", PLANE_BOX, _in_plane(f'<path class="{paint}" d="{outer}"/>'),
                      dim=False, frame=PLANE_BOX)
        out.append(_moving(cls, PLANE_BOX, _in_plane(f'<path class="{paint}" d="{inner}"/>'),
                           "plane tree", after=tip, frame=PLANE_BOX))
    return "".join(out)


def _slopes(wing, w):
    """The inner and the outer panel's slope (units up the picture per unit
    out along the span) that carry the tip w units up the picture with the
    cut on the first mode. The outer's slope is taken about the cut and is
    then sheared again by the inner's, whose shear also moves points along
    the span (the near wing points almost straight down); both are solved
    exactly, so the tip lands where the envelope puts it."""
    _, _, _, _, (sx, sy), ec, et = _wing(wing)
    a_in = w * _mode(ec / et) / ec
    a_out = (w - a_in * et) / ((et - ec) * (1 - a_in * sy))
    return a_in, a_out


def _shear(a, out):
    """A shear that moves each point a times its distance out along the
    span up the picture, as CSS: skewY then scaleY, about the pivot."""
    sx, sy = out
    return f"transform:skewY({_dec(math.degrees(math.atan(-a * sx)), 2)}deg) scaleY({_dec(1 - a * sy, 4)})"


def _wing_kf(name, wing, panel):
    """One panel's flex as @keyframes (panel 0 the inner, 1 the outer): the
    swings of the vibration, an extreme every half period, joined by half a
    cosine (the rule's own easing) and by a quarter from rest and back."""
    out = _wing(wing)[4]
    stops = []
    for t, v, spline in _swings(WING_P, _wing_env):
        ease = None if spline in (SINE_INOUT, None) else f"cubic-bezier({spline.replace(' ', ',')})"
        stops.append((t, _shear(_slopes(wing, v)[panel], out), ease))
    return _kf(name, stops)


PUFF = 10           # the smoke's period, seconds
PUFF_FROM, PUFF_TO = (0, 0, 0.5), (38, -80, 1.5)   # dx, dy, scale over one rise
PUFF_BOX = (1080, 346, 24, 24)                      # one puff, r 12 at (1092, 358)


def _puff_at(f):
    """Where a puff is at fraction f of its rise, and how opaque."""
    dx, dy, s = (a + (b - a) * f for a, b in zip(PUFF_FROM, PUFF_TO))
    op = min(1.0, f / 0.15, (1 - f) / 0.35)
    return dx, dy, s, op


def _puff_tf(dx, dy, s):
    return f"translate({_p(dx / PUFF_BOX[2] * 100)}%,{_p(dy / PUFF_BOX[3] * 100)}%) scale({s:.3f})"


def _smoke():
    """Five puffs of one rise from the chimney top, each a fifth of the way on
    from the one below. At rest they sit where the rise puts them at t = 0."""
    out = []
    for k in range(5):
        dx, dy, s, op = _puff_at((k + 0.5) / 5)
        out.append(_moving("mpf", PUFF_BOX, '<circle class="hpf" cx="1092" cy="358" r="12"/>',
                           "chimney tree",
                           style=f"--p:{k};transform:{_puff_tf(dx, dy, s)};opacity:{op:.2f}"))
    return "".join(out)


def _arcs():
    """The acoustic source at the tall building's foot."""
    return ('<path class="hs-h hf-n" stroke-width="1.5" d="M209.6 520A53 53 0 0 1 306.4 520"/>'
            '<path class="hs-s hf-n" stroke-width="1.8" d="M237 530A23.7 23.7 0 0 1 279.5 530"/>'
            '<circle class="hf-m" cx="258" cy="541" r="3.2"/>')


HILL = ("M-10 470L20 468C80 458 140 452 200 461S320 471 380 453S520 437 600 444S740 453 800 441"
        "S900 402 980 397S1080 390 1130 396S1220 414 1280 418L1300 420")
FAR_BOX = (-10, 380, 1310, 176)      # the far layer, sky to ground: the hills run past both edges


def _hills():
    """The far layer: hills and ghost blocks, the only layer the pointer moves.
    The hills run past both edges so the drift never shows an end."""
    return (f'<path fill="url(#ha-ghill)" opacity=".7" d="{HILL}V{G}H-10Z"/>'
            f'<path class="hs-h hf-n hns" stroke-width=".5" opacity=".55" d="{HILL}"/>'
            '<path class="hf-p" d="M24 468h46v87H24zM345 462h52v93h-52zM805 452h32v103h-32zM852 470h48v85h-48z'
            'M993 420h40v135h-40zM1112 468h66v87h-66zM1184 500h76v55h-76z"/>')


def _city():
    """The structures, back to front, and their reflection, which repeats
    them upside down through <use>, faded by paper laid over it. What moves
    in them moves by SMIL, whose values reach the clones, so the reflection
    moves with them; and as in the reference, a vehicle's reflection hides
    the reflections it passes in front of (the tower legs, the chimney's
    base). The rotor, the smoke and the airplane are layers over the drawing
    (_riders)."""
    front, back = [], []

    def both(pid, keys, build):
        front.append(_grp(keys, f'<g id="ha-{pid}">{build()}</g>'))
        back.append(_grp(keys, f'<use href="#ha-{pid}"/>'))

    both("b1", "low reg", _b1)
    both("b2", "tall reg", _b2)
    both("arc", "tall reg", _arcs)
    both("tw", "bridge nn", _towers)
    both("dk", "bridge nn", _deck)
    front.append(_grp("bridge nn", _wave()))
    both("tb", "turbine tree", _mast)
    both("b3", "mid nn", _b3)
    both("mb", "masonry tree", _masonry)
    both("cm", "chimney tree", _chimney)
    both("trn", "train nn", lambda: _travel(_train_moves(), _train(), "ha-ctrn"))
    both("car", "car tree", lambda: _travel(_car_moves(), _car()))
    return ("".join(front),
            '<g class="hrefl" clip-path="url(#ha-crefl)"><g transform="matrix(1 0 0 -1 0 1110)">'
            + "".join(back) + '</g></g><rect x="20" y="555" width="1260" height="196" fill="url(#ha-gfade)"/>')


# ------------------------------------------------------------------- the links

def _seg(a, b):
    (x1, y1), (x2, y2) = SENSORS[a], SENSORS[b]
    return f"M{_n(x1)} {_n(y1)}L{_n(x2)} {_n(y2)}"


# Every link is drawn in the direction its data flows. (from, to, keys, lets
# go with: b train, c car)
MESH = [
    ("b1", "b2", "low reg", ""), ("b2", "b3", "", ""), ("b3", "tl", "", ""),
    ("tn", "tl", "train nn", "b"), ("tn", "tr", "", "b"), ("tr", "hub", "", ""),
    ("hub", "rb", "turbine tree", ""), ("car", "rb", "", "c"), ("car", "ch", "car tree", "c"),
    ("ch", "pl", "car chimney tree", ""),
]
FAINT = [("b2", "tl", "", ""), ("tr", "tl", "bridge nn", ""), ("tr", "ch", "", ""),
         ("rb", "pl", "turbine masonry tree", ""), ("car", "pl", "", "c"), ("b1", "b3", "", "")]
# the climbs from a sensor to a model
UP = {
    "u1": ("M218 308L168 222", "low tall reg"),
    "u2": ("M312 378Q318 262 353 194", "mid nn"),
    "u3": ("M481 326C478 272 432 214 363 196", "bridge train nn"),
    "u6": ("M1066 231Q870 150 650 98.5", "turbine masonry car chimney plane tree"),
}
# between the models: regression to network, network to tree
MODEL_LINKS = (("M220 165L352 152", "nn"), ("M493 152C540 152 588 124 619 98.5", "tree"))
# the resting packets the reference shows on four links
DOTS = ((511.5, 421.5, "train nn", "b"), (886, 370.7, "turbine tree", ""),
        (319.7, 302.7, "mid nn", ""), (446.8, 247.5, "bridge train nn", ""))


def _link(d, cls, keys):
    k = f' data-k="{keys}"' if keys else ""
    return f'<path class="{cls} hdim"{k} d="{d}"/>'


def _links():
    plain, let = [], {"b": [], "c": []}

    def put(el, lt):
        (let[lt] if lt else plain).append(el)

    for d, keys in MODEL_LINKS:
        put(_link(d, "hl hl2", keys), "")
    for a, b, keys, lt in FAINT:
        put(_link(_seg(a, b), "hf", keys), lt)
    for a, b, keys, lt in MESH:
        put(_link(_seg(a, b), "hl", keys), lt)
    for key, (d, keys) in UP.items():
        put(_link(d, "hl hl2" if key == "u6" else "hl", keys), "")
    for x, y, keys, lt in DOTS:
        k = f' data-k="{keys}"' if keys else ""
        put(f'<circle class="hdot hdim"{k} cx="{_n(x)}" cy="{_n(y)}" r="2.8"/>', lt)
    # a link that hangs on a vehicle lets go while it is away, on a wrapper,
    # so the path itself stays free to brighten when a key lights it
    return ("".join(plain) + f'<g class="hlet-b">{"".join(let["b"])}</g>'
            f'<g class="hlet-c">{"".join(let["c"])}</g>')


# ------------------------------------------------------------------ the models

SQUARES = ((72.7, 85.7), (106, 90.7), (101.7, 99.3), (98.3, 110.7), (96.7, 119), (132.3, 109.7),
           (157, 82.3), (174.3, 90), (185.7, 84.3), (198.3, 81), (163.7, 101.7), (155, 109.3),
           (51.7, 141.3), (54, 150), (82, 148.3))
CIRCLES = ((121.7, 173), (133, 187.7), (145, 195.7), (82.3, 189), (162.3, 207), (171, 208),
           (193.3, 180), (199.3, 200.3), (186.7, 132.7), (171.3, 142.7), (166.3, 147),
           (144.3, 155.7), (52, 202.7), (55.3, 205), (51.7, 211.7), (93.3, 209.3))
RINGED = ((87.3, 174.3, "o"), (107.7, 142.7, "s"), (166.7, 109.3, "s"), (184, 119, "o"))
NEWPT = (141, 143.3)
FIT_BOX = (45, 82.9, 167, 115.4)     # the band's box: its centre (128.5, 140.6) is the fit's pivot
PTS_BOX = (40, 70, 172, 150)
REG_KEYS = "low tall reg nn"


def _sq(x, y, s=7.4):
    return f"M{_n(x - s / 2)} {_n(y - s / 2)}h{_n(s)}v{_n(s)}h-{_n(s)}z"


def _regression():
    """The fit tips and settles (a layer that rotates, its band a layer in it
    that breathes); the points lie over it as a still layer, and the new
    point drops in over them."""
    band = '<path class="hf-p" d="M45 178.3L212 82.9V102.9L45 198.3Z"/>'
    lines = ('<path class="hs-h hf-n" stroke-width="1.2" stroke-dasharray="4 3.5" '
             'd="M45 178.3L212 82.9M45 198.3L212 102.9"/>'
             '<path class="hs-m hf-n" stroke-width="2.4" stroke-linecap="round" d="M45 188.3L212 92.9"/>')
    fit = _moving("mfit", FIT_BOX, lines, REG_KEYS, under=_mover("mbd", FIT_BOX, band, FIT_BOX))
    halo = "".join(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="9.5"/>' for x, y, _ in RINGED)
    sq = "".join(_sq(x, y) for x, y in SQUARES) + "".join(_sq(x, y) for x, y, k in RINGED if k == "s")
    dots = "".join(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="3.4"/>' for x, y in CIRCLES)
    dots += "".join(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="3.6"/>' for x, y, k in RINGED if k == "o")
    pts = _still(PTS_BOX, f'<g class="hhalo">{halo}</g><path class="hf-w hs-m" stroke-width="1.5" '
                          f'd="{sq}"/><g class="hf-m">{dots}</g>', REG_KEYS)
    x, y = NEWPT
    nh = _moving("mnh", (x - 9.5, y - 9.5, 19, 19),
                 f'<circle class="hhalo" cx="{x}" cy="{y}" r="9.5"/>', REG_KEYS)
    npt = _moving("mnp", (x - 5, y - 5, 10, 10), f'<circle class="hf-m" cx="{x}" cy="{y}" r="3.6"/>', REG_KEYS)
    return fit + pts + nh + npt


L1 = [(358, 115), (358, 152), (358, 189)]
L2 = [(422, 97), (422, 134), (422, 171), (422, 207)]
L3 = [(487, 115), (487, 152), (487, 189)]
NN_FILL = {("L2", 0): "hf-m", ("L2", 2): "hf-m", ("L3", 1): "hf-m", ("L1", 1): "hf-s"}


def _nn():
    """The network: the edges as two fans and the nodes as three layers, each
    lighting as one (opacity), so a forward pass is five changes."""
    fans = ["".join(f"M{x1} {y1}L{x2} {y2}" for x1, y1 in a for x2, y2 in b)
            for a, b in ((L1, L2), (L2, L3))]
    glow = "".join(f'<g class="hnl hnl{k}">' + "".join(f'<circle cx="{x}" cy="{y}" r="10.5"/>'
                                                      for x, y in layer) + "</g>"
                   for k, layer in enumerate((L1, L2, L3), 1))
    nodes = "".join(f'<circle class="{NN_FILL.get((name, k), "hf-w")}" cx="{x}" cy="{y}" r="5.6"/>'
                    for name, layer in (("L1", L1), ("L2", L2), ("L3", L3))
                    for k, (x, y) in enumerate(layer))
    return (f'<path class="hs-h hf-n hns" stroke-width=".5" d="{"".join(fans)}"/>'
            f'<path class="hne hne1" d="{fans[0]}"/><path class="hne hne2" d="{fans[1]}"/>'
            f'{glow}<g class="hs-m" stroke-width="2">{nodes}</g>')


ROOT, LEFT, RIGHT = (634.5, 98.5, 15.5), (577.5, 154.5, 14), (691.5, 154.5, 14)
LEAVES = (550, 608.5, 664, 719.5)
TREE_KEYS = "turbine masonry car chimney plane tree"


def _diamond(cx, cy, h):
    return f"M{_n(cx)} {_n(cy - h)}L{_n(cx + h)} {_n(cy)}L{_n(cx)} {_n(cy + h)}L{_n(cx - h)} {_n(cy)}Z"


def _leaf(cx, cy=207, w=17, h=14, r=4):
    x, y = cx - w / 2, cy - h / 2
    return (f"M{_n(x + r)} {_n(y)}h{_n(w - 2 * r)}a{r} {r} 0 0 1 {r} {r}v{_n(h - 2 * r)}"
            f"a{r} {r} 0 0 1 -{r} {r}h-{_n(w - 2 * r)}a{r} {r} 0 0 1 -{r} -{r}v-{_n(h - 2 * r)}"
            f"a{r} {r} 0 0 1 {r} -{r}z")


def _tree():
    rx, ry, rh = ROOT
    lx, ly, lh = LEFT
    qx, qy, qh = RIGHT
    base = (f"M{rx} {ry + rh}L{lx} {ly - lh}M{rx} {ry + rh}L{qx} {qy - qh}"
            f"M{lx} {ly + lh}L550 200M{lx} {ly + lh}L608.5 200"
            f"M{qx} {qy + qh}L664 200M{qx} {qy + qh}L719.5 200")
    leaves = "".join(_leaf(x) for x in LEAVES)
    return (f'<path class="hs-h hf-n hns" stroke-width=".6" d="{base}"/>'
            f'<path class="hf-w hs-h" stroke-width="1.6" d="{leaves}"/>'
            f'<path class="hf-w hs-m" stroke-width="2" d="{_diamond(*ROOT)}{_diamond(*LEFT)}{_diamond(*RIGHT)}"/>')


def _tree_path():
    """The tree's answer, which the story takes away and gives back, root to
    leaf: each part a layer that fades and settles by scale; an edge grows out
    of the node that passes the answer on. Then the insight: the leaf turns
    amber and one amber ring leaves it."""
    rx, ry, rh = ROOT
    qx, qy, qh = RIGHT

    def lit(cls, box, d):
        return _moving(cls, box, f'<path class="hlit" d="{d}"/>', TREE_KEYS)
    ins = (706, 195, 27, 24)
    return (lit("mt1", (rx - rh, ry - rh, 2 * rh, 2 * rh), _diamond(*ROOT))
            + lit("mdr1", (rx, ry + rh, qx - rx, qy - qh - ry - rh), f"M{rx} {ry + rh}L{qx} {qy - qh}")
            + lit("mt3", (qx - qh, qy - qh, 2 * qh, 2 * qh), _diamond(*RIGHT))
            + lit("mdr2", (qx, qy + qh, 719.5 - qx, 200 - qy - qh), f"M{qx} {qy + qh}L719.5 200")
            + _moving("mins", ins, f'<path class="hah" d="{_leaf(719.5, 207, 27, 24, 7)}"/>'
                                   f'<path class="hac" d="{_leaf(719.5)}"/>', TREE_KEYS)
            + _moving("mip", ins, f'<path class="hip" d="{_leaf(719.5, 207, 27, 24, 7)}"/>', TREE_KEYS))


# ----------------------------------------------------------------- the sensors

def _ring(x, y, strong=False):
    """A sensor: a pale halo and a paper-white ring in --link."""
    return (f'<g class="{"hfire" if strong else "hsoft"}"><circle class="hhalo" cx="{_n(x)}" '
            f'cy="{_n(y)}" r="10.5"/><circle class="hrg" cx="{_n(x)}" cy="{_n(y)}" r="5.6"/></g>')


# when each sensor speaks: a story sensor fires (strong), the others breathe
# (soft), left to right, in step with the story. A relay fires the moment the
# packet reaches it, so its time is the packet's arrival.
FIRE = {"b2": 0.62, "tn": 5.25, "tl": 5.4, "car": 8.85, "ch": 9.3, "pl": 9.7}
SOFT = {"b1": 0.35, "b3": 1.05, "tr": 5.6, "hub": 7.0, "rb": 7.4}
RIDERS = ("pl", "hub")   # sensors drawn on a layer over the drawing, which moves


def _pulse(name, x, y, frame=VB):
    """A sensor's pulse: a ring that spreads from under it and fades, a layer
    of its own (it rides on the airplane's mover). The train's and the car's
    stand where their vehicle parks: each fires only while it is parked."""
    t = FIRE.get(name, SOFT.get(name))
    box = (x - 8, y - 8, 16, 16)
    mv = _mover("mq" + (" mqf" if name in FIRE else ""), box,
                f'<circle class="hq" cx="{_n(x)}" cy="{_n(y)}" r="5.6"/>', style=f"--d:{t - T:.2f}s")
    return _layer(box, mv, SENSOR_KEYS[name], frame=frame)


def _sensors():
    """The rings, over the links: the tall building's leans with its roof,
    the train's and the car's travel with them (the train's twice, one on
    each train of the pair), the rotor's and the airplane's ride on their
    layers."""
    def ring(name, x, y):
        r = _ring(x, y, name in FIRE)
        if name == "tn":
            return _travel(_train_moves(), r + _ring(x - SHIFT, y, True), "ha-ctrn")
        if name == "car":
            return _travel(_car_moves(), r)
        return _lean("", r) if name == "b2" else r
    return "".join(_grp(SENSOR_KEYS[name], ring(name, x, y))
                   for name, (x, y) in SENSORS.items() if name not in RIDERS)


def _arc_box(x0, x1, y, r):
    """The box of an arc that rises over the chord x0..x1 at y, radius r."""
    half = (x1 - x0) / 2
    top = y - (r - math.sqrt(r * r - half * half))
    return (round(x0, 1), round(top, 1), round(x1 - x0, 1), round(y - round(top, 1), 1))


EMITTERS = (   # the acoustic source in beat A, the car's hum in beat C
    ("mem", "tall reg", "hs-s", 1.8, (237, 279.5, 530, 23.7)),
    ("mem mem2", "tall reg", "hs-h", 1.5, (209.6, 306.4, 520, 53)),
    ("mhum", "car tree", "hs-s", 1.8, (1006, 1054, 520, 30)),
    ("mhum mhum2", "car tree", "hs-h", 1.5, (992, 1068, 512, 48)),
)


def _emitters():
    out = []
    for cls, keys, paint, sw, (x0, x1, y, r) in EMITTERS:
        d = f"M{_n(x0)} {_n(y)}A{_n(r)} {_n(r)} 0 0 1 {_n(x1)} {_n(y)}"
        out.append(_moving(cls, _arc_box(x0, x1, y, r),
                           f'<path class="{paint} hf-n" stroke-width="{sw}" d="{d}"/>', keys))
    return "".join(out)


# ------------------------------------------------------------------ the packets

def _pts(d):
    """The points of a one-segment path: M then L, Q or C."""
    nums = [float(v) for v in d.replace("M", " ").replace("L", " ").replace("Q", " ")
            .replace("C", " ").split()]
    return list(zip(nums[0::2], nums[1::2]))


def _at(pts, t):
    u = 1 - t
    if len(pts) == 2:
        (x0, y0), (x1, y1) = pts
        return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
    if len(pts) == 3:
        (x0, y0), (x1, y1), (x2, y2) = pts
        return u * u * x0 + 2 * u * t * x1 + t * t * x2, u * u * y0 + 2 * u * t * y1 + t * t * y2
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pts
    return (u ** 3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t ** 3 * x3,
            u ** 3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t ** 3 * y3)


def _along(pts, s):
    """The point a fraction s of the way along the path, by arc length."""
    ps = [_at(pts, i / 240) for i in range(241)]
    acc = [0.0]
    for p, q in zip(ps, ps[1:]):
        acc.append(acc[-1] + math.dist(p, q))
    goal = s * acc[-1]
    for i in range(1, 241):
        if acc[i] >= goal:
            f = (goal - acc[i - 1]) / ((acc[i] - acc[i - 1]) or 1)
            p, q = ps[i - 1], ps[i]
            return p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f
    return ps[-1]


def _bezier(x1, y1, x2, y2):
    """A CSS cubic-bezier as a function of progress, for sampling a path."""
    def coord(t, a, b):
        return 3 * a * t * (1 - t) ** 2 + 3 * b * t * t * (1 - t) + t ** 3

    def ease(u):
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if coord(mid, x1, x2) < u:
                lo = mid
            else:
                hi = mid
        return coord((lo + hi) / 2, y1, y2)
    return ease


PACKETS = [  # (path, start s, travel s, keys)
    (UP["u1"][0], 0.72, 0.62, "low tall reg"),
    (UP["u3"][0], 5.5, 0.9, "bridge train nn"),
    (_seg("car", "ch"), 8.95, 0.35, "car tree"),
    (_seg("ch", "pl"), 9.4, 0.3, "car chimney tree"),
    (UP["u6"][0], 9.8, 0.8, "turbine masonry car chimney plane tree"),
]
PK = 20             # a packet's box, units: its motion is in percent of it


def _packets():
    """Each packet is a dot with a soft halo, half as large again as the
    resting dots on the links (r 4.8 against 2.8), so at the desktop size a
    packet on its way reads as data moving, not as one more dot."""
    out = []
    for i, (d, _, _, keys) in enumerate(PACKETS):
        x, y = _pts(d)[0]
        out.append(_moving(f"mpk mpk{i}", (x - PK / 2, y - PK / 2, PK, PK),
                           f'<circle class="hpg" cx="{_n(x)}" cy="{_n(y)}" r="9"/>'
                           f'<circle class="hpd" cx="{_n(x)}" cy="{_n(y)}" r="4.8"/>', keys))
    return "".join(out)


# ------------------------------------------------------------ signal, spectrum

TAPE = 630          # the trace's period, units: 12 s at 52.5 units a second
SPEED = TAPE / T
RIP = (681, 820)    # the ripple, where the trace ends and the spectrum starts
# when a burst reaches the ripple: every 4 s, which puts the bursts of the
# picture at rest at x 75, 285 and 495 and their bumps 95 units to the right,
# where the reference has them
ANSWERS = (3.55, 7.55, 11.55)
BUMP_LEAD = 95 / 52.5   # a burst's slow bump arrives this much earlier
# The ripple's and the bars' clocks start here (seconds of story time), so no
# ring or breath runs past the end of their own 12 s cycle: the last answer,
# the loudest, spreads and settles in full instead of being cut at 12 s.
RIP_T0 = 3.25
BAR_T0 = 1.5


def _tape_y(x):
    y = 0.0
    for t_ans in ANSWERS:
        c = RIP[0] + TAPE - SPEED * t_ans     # tape position of the burst at t=0
        for cc in (c - TAPE, c, c + TAPE):
            u = x - cc
            y -= 16.5 * math.sin(2 * math.pi * u / 8.4) * math.exp(-(u / 9.5) ** 2)
            b = cc + SPEED * BUMP_LEAD           # the bump sits to the right
            v = x - b
            if v > 0:
                y -= 15.5 * (v / 5.2) * math.exp(1 - v / 5.2)
                if v > 14:
                    y -= 2.4 * math.sin(2 * math.pi * (v - 14) / 17) * math.exp(-(v - 14) / 20)
            y += 2.6 * math.exp(-((v + 6) / 5) ** 2)
    y += 0.7 * math.sin(x / 6.1) * math.sin(x / 21.7 + 1.3)
    return y


def _tape_d():
    xs = []
    x = 0.0
    events = []
    for t_ans in ANSWERS:
        c = RIP[0] + TAPE - SPEED * t_ans - TAPE
        while c < TAPE + 30:
            events.append(c)
            c += TAPE
    while x <= TAPE + 0.01:
        near = any(-24 <= x - c <= 24 for c in events) or \
            any(-10 <= x - (c + SPEED * BUMP_LEAD) <= 60 for c in events)
        xs.append(x)
        x += 1.6 if near else 5.5
    return "M" + " ".join(f"{_n(x)} {_n(RIP[1] + _tape_y(x))}" for x in xs)


BARS = (32, 38, 29, 35, 33, 22, 20, 27, 36, 29, 21, 18, 20, 17, 18, 21, 27, 19, 11, 11,
        17, 17, 12, 18, 18, 18, 9, 12, 11, 12, 10, 12, 16, 11, 8, 7)
BAR_GROUP = 3       # bars that breathe as one; the groups answer left to right
BAR_STEP = 0.075    # seconds from one group to the next: 25 ms a bar
BAR_Y, BAR_H = 778, 64      # a group's box, top and height: the axis lies 42 units down it


def _bars():
    """The spectrum, in groups that breathe as one, each a layer that scales
    from the axis, with its own faint reflection (a <use> of its bars,
    flattened under the axis) inside it, so the reflection breathes with it."""
    out = []
    ry = RIP[1]
    for g in range(len(BARS) // BAR_GROUP):
        band = "mbl" if g < 4 else ("mbm" if g < 8 else "mbh")
        rects = []
        for i in range(g * BAR_GROUP, (g + 1) * BAR_GROUP):
            x = 703 + 15.43 * i
            cls = "hf-m" if i % 5 == 0 else ("hf-s" if i % 2 else "hf-t")
            rects.append(f'<rect class="{cls}" x="{_n(x - 2.2)}" y="{_n(ry - BARS[i])}" '
                         f'width="4.4" height="{BARS[i]}" rx="2.2"/>')
        x0 = round(703 + 15.43 * g * BAR_GROUP - 3.5, 1)
        out.append(_moving(f"mbg {band}", (x0, BAR_Y, 37.9, BAR_H),
                           f'<g id="ha-bg{g}">{"".join(rects)}</g><use href="#ha-bg{g}" opacity=".22" '
                           f'transform="matrix(1 0 0 -.4 0 {_n(ry * 1.4 + 2)})"/>',
                           style=f"--d:{g * BAR_STEP + BAR_T0:.3f}s"))
    return "".join(out)


# ------------------------------------------------------------ the layers, in order

PLANE_BOX = (968, 148, 204, 164)
ROTOR_BOX = (722, 232, 240, 240)     # centred on the hub


def _riders():
    """The layers that ride over the city: the rotor, the smoke and the
    airplane with its wings, each with the sensor it carries; and the paper
    at the road's end, under which the car drives out of the picture."""
    hub, pl = SENSORS["hub"], SENSORS["pl"]
    rotor = _moving("mrot", ROTOR_BOX, _blades() + _ring(*hub), "turbine tree")
    plane = _moving("mfl", PLANE_BOX, _grp("plane tree", _plane()) + _grp(SENSOR_KEYS["pl"], _ring(*pl, True)),
                    after=_pulse("pl", *pl, PLANE_BOX), dim=False, under=_wings())
    x0, _, w, _ = VB
    road = _fade((1226, 500, x0 + w - 1226, 100),
                 "linear-gradient(90deg,transparent 3.704%,var(--page) 70.37%)")
    return rotor + _pulse("hub", *hub) + _smoke() + plane + road


def _tape():
    """The trace in the drawing, three turns of the tape and their faint
    reflection under the axis, scrolling one turn a loop inside its clip."""
    ry = RIP[1]
    tape = (f'<path id="ha-tp" class="hs-m hf-n htr" stroke-width="1.5" stroke-linejoin="round" '
            f'd="{_tape_d()}"/><use href="#ha-tp" x="{TAPE}"/><use href="#ha-tp" x="{2 * TAPE}"/>'
            f'<g opacity=".2" transform="matrix(1 0 0 -1 0 {2 * ry})"><use href="#ha-tp"/>'
            f'<use href="#ha-tp" x="{TAPE}"/><use href="#ha-tp" x="{2 * TAPE}"/></g>')
    return _grp("", _travel([(0, -TAPE, LINEAR), (T, 0, None)], tape, "ha-ctape"))


def _signal_layers():
    """Over the trace: the paper at both its ends, the ripple's still rings,
    the ring that spreads, the bars, the ring that pops."""
    rx, ry = RIP
    rings = (f'<path class="hs-t hf-n hns" stroke-width=".5" d="M672 {ry}H1248"/>'
             f'<g class="hf-n hns"><circle class="hs-t" stroke-width=".45" cx="{rx}" cy="{ry}" r="51"/>'
             f'<circle class="hs-s" stroke-width=".5" cx="{rx}" cy="{ry}" r="30"/>'
             f'<circle class="hs-t" stroke-width=".45" cx="{rx}" cy="{ry}" r="16"/></g>')
    return (_fade((20, 788, 64, 64), "linear-gradient(90deg,var(--page) 56%,transparent)")
            + _fade((672, 788, 9, 64), "linear-gradient(90deg,transparent,var(--page))")
            + _still((628, 766, 622, 108), rings)
            + _moving("mrip", (rx - 10, ry - 10, 20, 20),
                      f'<circle class="hs-m hf-n" stroke-width="1.4" cx="{rx}" cy="{ry}" r="8"/>')
            + _bars()
            + _moving("mrgc", (rx - 9, ry - 9, 18, 18), f'<circle class="hrg" cx="{rx}" cy="{ry}" r="5.2"/>'))


# ---------------------------------------------------------------------- defs

def _defs():
    x0, y0, w, h = VB
    return (
        "<defs>"
        '<linearGradient id="ha-gb1" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" class="hgs-t"/><stop offset="1" class="hgs-p"/></linearGradient>'
        # the tall building's, in user space: its two blocks share it
        f'<linearGradient id="ha-gb2" gradientUnits="userSpaceOnUse" x1="0" y1="308" x2="0" y2="{G}">'
        '<stop offset="0" class="hgs-s"/><stop offset="1" class="hgs-t"/></linearGradient>'
        '<linearGradient id="ha-grb" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" class="hgs-t"/><stop offset="1" class="hgs-p"/></linearGradient>'
        '<linearGradient id="ha-ghill" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" class="hgs-p" stop-opacity=".9"/>'
        '<stop offset="1" class="hgs-p" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="ha-gground" gradientUnits="userSpaceOnUse" x1="40" y1="0" x2="1262" y2="0">'
        '<stop offset="0" class="hgs-i" stop-opacity="0"/><stop offset=".05" class="hgs-i"/>'
        '<stop offset=".95" class="hgs-i"/><stop offset="1" class="hgs-i" stop-opacity="0"/>'
        "</linearGradient>"
        '<linearGradient id="ha-grail" gradientUnits="userSpaceOnUse" x1="300" y1="0" x2="915" y2="0">'
        '<stop offset="0" class="hgs-i" stop-opacity="0"/><stop offset=".07" class="hgs-i"/>'
        '<stop offset=".93" class="hgs-i"/><stop offset="1" class="hgs-i" stop-opacity="0"/>'
        "</linearGradient>"
        # Paper laid over the reflection, away from the ground line: a
        # gradient of --page, not a mask. The reflection is clipped just
        # short of where its paper ends, so the two edges never share a row.
        f'<clipPath id="ha-crefl"><rect x="{x0}" y="{G}" width="{w}" height="190"/></clipPath>'
        '<linearGradient id="ha-gfade" gradientUnits="userSpaceOnUse" x1="0" y1="555" x2="0" y2="745">'
        '<stop offset="0" class="hgs-pg" stop-opacity=".5"/><stop offset="1" class="hgs-pg"/>'
        '</linearGradient>'
        # where the train passes out of sight behind the two buildings, and
        # where the trace does at the picture's edge and in the ripple; the
        # reflection's clone of the train turns its clip upside down with it
        f'<clipPath id="ha-ctrn"><rect x="{TRAIN_CLIP[0]}" y="{TRAIN_CLIP[1]}" '
        f'width="{TRAIN_CLIP[2]}" height="{TRAIN_CLIP[3]}"/></clipPath>'
        f'<clipPath id="ha-ctape"><rect x="{TAPE_CLIP[0]}" y="{TAPE_CLIP[1]}" '
        f'width="{TAPE_CLIP[2]}" height="{TAPE_CLIP[3]}"/></clipPath>'
        # the room between the main span's cable and deck, which bends with them
        f'<clipPath id="ha-cgap"><path d="{GAP}">{_span_smil(gap=True)}</path></clipPath>'
        "</defs>")


# ----------------------------------------------------------------- the markup

LABEL = ("Sensors on buildings, a suspension bridge, a train, a wind turbine, a car, a chimney "
         "and an airplane send their data to a regression, a neural network and a decision "
         "tree; below, a signal runs into a ripple and becomes a spectrum.")

# The keys a pointer, a finger or the keyboard can light: (key, name, box in
# JPEG units x0 y0 x1 y1, the model it feeds or None for a model, what it says)
KEYS = (
    ("low", "Low-rise building", (68, 400, 166, 557), "reg",
     "Its sensor passes data through the tall building's sensor to the regression."),
    ("tall", "Tall building", (170, 294, 266, 557), "reg",
     "Its sensor sends data to the regression. A sound source rings at its foot."),
    ("mid", "Mid-rise building", (270, 364, 352, 557), "nn",
     "Its sensor sends data to the neural network."),
    ("bridge", "Suspension bridge", (398, 312, 800, 492), "nn",
     "Sensors on its towers send data to the neural network."),
    ("train", "Train", (352, 500, 818, 572), "nn",
     "A sensor on the train sends data to the neural network."),
    ("turbine", "Wind turbine", (806, 236, 892, 557), "tree",
     "A sensor at the hub sends data to the decision tree."),
    ("masonry", "Masonry building", (900, 385, 994, 557), "tree",
     "Its sensor sends data to the decision tree."),
    ("car", "Car", (958, 500, 1102, 572), "tree",
     "A sensor on the car sends data to the decision tree."),
    ("chimney", "Chimney", (1062, 288, 1146, 556), "tree",
     "Its sensor sends data to the decision tree."),
    ("plane", "Airplane", (968, 180, 1156, 298), "tree",
     "Its sensor sends data to the decision tree."),
    ("reg", "Regression", (34, 72, 226, 224), None,
     "Data from the low-rise and the tall building. Its result goes on to the neural network."),
    ("nn", "Neural network", (338, 84, 508, 218), None,
     "Data from the mid-rise building, the suspension bridge and the train. Its result goes on "
     "to the decision tree."),
    ("tree", "Decision tree", (530, 78, 742, 228), None,
     "Data from the wind turbine, the masonry building, the car, the chimney and the airplane."),
)


def _place(box):
    """A key's box as percentages of the figure, centred on its middle, so the
    24px floor (WCAG 2.2 SC 2.5.8) grows it evenly on a phone."""
    x0, y0, x1, y1 = box
    vx, vy, vw, vh = VB
    return (f"left:{((x0 + x1) / 2 - vx) / vw * 100:.2f}%;top:{((y0 + y1) / 2 - vy) / vh * 100:.2f}%;"
            f"width:{(x1 - x0) / vw * 100:.2f}%;height:{(y1 - y0) / vh * 100:.2f}%")


_ARROW = ('<svg class="ha__arr" viewBox="0 0 24 24" width="14" height="14" fill="none" '
          'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" '
          'aria-hidden="true" focusable="false"><path d="M4.5 12h14.5"/><path d="m13.5 6.5 5.5 5.5-5.5 5.5"/></svg>')


def _keys():
    feeds = {m: sum(1 for k in KEYS if k[3] == m) for m in ("reg", "nn", "tree")}
    buttons, notes = [], []
    for i, (key, name, box, to, note) in enumerate(KEYS):
        rel = f' data-to="{to}"' if to else f' data-n="{feeds[key]}"'
        buttons.append(f'<button class="ha__key" type="button" data-key="{key}"{rel} aria-pressed="false" '
                       f'aria-describedby="ha-d-{key}" tabindex="{0 if i == 0 else -1}" '
                       f'style="{_place(box)}"><span class="ha__sr">{name}</span></button>')
        notes.append(f'<span id="ha-d-{key}">{note}</span>')
    return ('<div class="ha__keys" role="toolbar" aria-label="Trace the data" hidden>'
            + "".join(buttons) + "</div><div hidden>" + "".join(notes) + "</div>")


_MARKUP = []


def render():
    """Return the complete figure: the drawing, the layers that move over it,
    its keys, and the line under it that names what is lit."""
    if _MARKUP:
        return _MARKUP[0]
    x0, y0, w, h = VB
    city, refl = _city()
    # the far hills under the drawing: the one layer the pointer moves. The
    # hills run past both edges, where the figure clips them.
    far = _layer(FAR_BOX, _mover("ha__far", FAR_BOX, _hills()), cls="ha-far")
    svg = (f'<svg class="ha__svg" viewBox="{x0} {y0} {w} {h}" width="{w}" height="{h}" '
           f'role="img" aria-label="{LABEL}" focusable="false">'
           + _defs()
           + refl
           + _grp("", f'<path class="hf-n hns" stroke="url(#ha-gground)" stroke-width=".8" d="M40 {G}.5H1262"/>')
           + _grp("train nn", _rail())
           + city
           + _links()
           + _grp(REG_KEYS, '<path class="hs-h hf-n hns" stroke-width=".6" d="M40.5 80V215H218"/>')
           + _grp("mid bridge train nn tree", _nn())
           + _grp(TREE_KEYS, _tree())
           + _sensors()
           + _grp("", f'<path class="hs-t hf-n hns" stroke-width=".5" d="M58 {RIP[1]}H1248"/>')
           + _tape()
           + "</svg>")
    fx = ('<div class="ha__fx" aria-hidden="true">'
          + _riders() + _regression() + _tree_path() + _emitters()
          + "".join(_pulse(n, *SENSORS[n]) for n in SENSORS if n not in RIDERS)
          + _packets() + _signal_layers() + "</div>")
    _MARKUP.append(
        f'<figure class="ha"><div class="ha__stage"><div aria-hidden="true">{far}</div>{svg}{fx}'
        f'{_keys()}</div>'
        f'<div class="ha__read" aria-hidden="true"><span class="ha__a"></span>{_ARROW}'
        f'<span class="ha__b"></span></div></figure>')
    return _MARKUP[0]


# ------------------------------------------------------------------ the motion

def _kf(name, stops):
    """@keyframes from (seconds after the animation starts, declarations,
    easing to the next stop) on the story's period."""
    body = []
    for t, decl, ease in stops:
        pct = max(0.0, min(100.0, t / T * 100))
        e = f";animation-timing-function:{ease}" if ease else ""
        body.append(f"{pct:.3f}".rstrip("0").rstrip(".") + f"%{{{decl}{e}}}")
    return f"@keyframes {name}{{{''.join(body)}}}"


OUT = "cubic-bezier(.2,.8,.2,1)"      # the site's --ease: things that travel and land
INOUT = "cubic-bezier(.45,0,.25,1)"   # a packet: leaves, cruises, arrives
SINE = "cubic-bezier(.37,0,.63,1)"    # a swell


def _pulses(events, attack=0.16, decay=0.95):
    """scaleY pulses for a band of bars; events are seconds from 0."""
    stops = [(0, "transform:scaleY(1)", None)]
    for t, a in sorted(events):
        end = t + decay
        stops.append((t, "transform:scaleY(1)", "cubic-bezier(.2,.7,.3,1)"))
        stops.append((t + attack, f"transform:scaleY({1 + a:.2f})", SINE))
        stops.append((end, "transform:scaleY(1)", None))
    stops.append((T, "transform:scaleY(1)", None))
    return stops


def _packet_stops(d, dur):
    """A packet along its link, in percent of its own box: a straight link is
    two stops on INOUT, a curve is sampled along its length on the same
    easing. Opacity rides on stops of its own."""
    pts = _pts(d)
    x0, y0 = pts[0]

    def tr(x, y):
        return f"transform:translate({_p((x - x0) / PK * 100)}%,{_p((y - y0) / PK * 100)}%)"
    stops = []
    if len(pts) == 2:
        x1, y1 = pts[1]
        stops.append((0, "transform:translate(0,0)", INOUT))
        stops.append((dur, tr(x1, y1), None))
    else:
        ease = _bezier(.45, 0, .25, 1)
        n = 12
        for i in range(n + 1):
            u = i / n
            x, y = _along(pts, ease(u))
            stops.append((dur * u, tr(x, y), "linear"))
    stops[-1] = (dur, stops[-1][1], None)
    end = stops[-1][1]
    stops += [(0.0001, "opacity:0", "linear"), (0.08, "opacity:1", "linear"),
              (dur - 0.1, "opacity:1", "linear"), (dur, "opacity:0", None), (T, end + ";opacity:0", None)]
    # merge the stops that land on the same moment
    merged = {}
    for t, decl, ease in sorted(stops, key=lambda s: s[0]):
        at = round(t, 4)
        decls, e = merged.get(at, ([], None))
        merged[at] = (decls + [decl], e or ease)
    return [(t, ";".join(ds), e) for t, (ds, e) in sorted(merged.items())]


def _motion_css():
    k = []
    # a sensor fires: a pulse spreads from under the ring and fades
    k.append(_kf("ha-fire", [(0, "opacity:.85;transform:scale(1)", OUT),
                             (0.9, "opacity:0;transform:scale(3.3)", None),
                             (T, "opacity:0;transform:scale(3.3)", None)]))
    k.append(_kf("ha-soft", [(0, "opacity:.45;transform:scale(1)", OUT),
                             (0.8, "opacity:0;transform:scale(2.3)", None),
                             (T, "opacity:0;transform:scale(2.3)", None)]))
    for i, (d, _, dur, _) in enumerate(PACKETS):
        k.append(_kf(f"ha-pk{i}", _packet_stops(d, dur)))
    # the emitters: the acoustic source in beat A, the car's hum in beat C
    k.append(_kf("ha-emit", [(0, "opacity:.9;transform:scale(.85)", OUT),
                             (1.2, "opacity:0;transform:scale(1.55)", None),
                             (T, "opacity:0;transform:scale(1.55)", None)]))
    # beat A: the regression takes a new point and refits (it drops 30 units)
    drop = f"translateY({_p(-30 / 10 * 100)}%)"
    k.append(_kf("ha-new", [(0, "opacity:1;transform:translateY(0)", OUT),
                            (0.15, "opacity:0;transform:translateY(0)", None),
                            (0.16, f"opacity:0;transform:{drop}", OUT),
                            (0.3, "opacity:1", None),
                            (0.95, "transform:translateY(0)", None),
                            (T, "opacity:1;transform:translateY(0)", None)]))
    k.append(_kf("ha-halo", [(0, "opacity:1;transform:scale(1)", OUT),
                             (0.15, "opacity:0;transform:scale(.5)", None),
                             (0.7, "opacity:0;transform:scale(.5)", OUT),
                             (1.2, "opacity:1;transform:scale(1)", None),
                             (T, "opacity:1;transform:scale(1)", None)]))
    k.append(_kf("ha-fit", [(0, "transform:rotate(0)", OUT), (0.3, "transform:rotate(-4.5deg)", OUT),
                            (1.35, "transform:rotate(0)", None), (T, "transform:rotate(0)", None)]))
    k.append(_kf("ha-band", [(0, "transform:scaleY(1)", OUT), (0.3, "transform:scaleY(1.4)", OUT),
                             (1.35, "transform:scaleY(1)", None), (T, "transform:scaleY(1)", None)]))
    # beat B: the trains pass (by SMIL, _train_moves); the links on the train
    # let go and take hold again
    k.append(_kf("ha-let", [(0, "opacity:1", None), (0.2, "opacity:0", None),
                            (2.5, "opacity:0", OUT), (2.9, "opacity:1", None), (T, "opacity:1", None)]))
    k.append(_kf("ha-wv", [(0, "opacity:0", OUT), (0.14, "opacity:1", SINE), (0.7, "opacity:0", None),
                           (T, "opacity:0", None)]))
    # the network: a layer lights, a fan of edges carries it on
    k.append(_kf("ha-flash", [(0, "opacity:0", OUT), (0.2, "opacity:1", SINE), (0.95, "opacity:0", None),
                              (T, "opacity:0", None)]))
    # beat C: the car drives off at the edge and comes back to park (by SMIL,
    # _car_moves); the links on the car let go while it is away
    k.append(_kf("ha-let-c", [(0, "opacity:1", None), (0.2, "opacity:0", None),
                              (2.9, "opacity:0", OUT), (3.2, "opacity:1", None), (T, "opacity:1", None)]))
    # the tree lets go of its answer and finds it again, root to leaf
    k.append(_kf("ha-t1", [(0, "opacity:1;transform:scale(1)", None), (0.3, "opacity:0", None),
                           (0.35, "opacity:0;transform:scale(1.18)", OUT),
                           (0.6, "opacity:1;transform:scale(1)", None), (T, "opacity:1", None)]))
    # an edge of the path grows out of the node that passes the answer on
    k.append(_kf("ha-dr1", [(0, "opacity:1;transform:scale(1)", None), (0.3, "opacity:0", None),
                            (0.45, "opacity:0;transform:scale(.35)", OUT),
                            (0.68, "opacity:1;transform:scale(1)", None),
                            (T, "opacity:1;transform:scale(1)", None)]))
    k.append(_kf("ha-t3", [(0, "opacity:1;transform:scale(1)", None), (0.3, "opacity:0", None),
                           (0.7, "opacity:0;transform:scale(1.18)", OUT),
                           (0.95, "opacity:1;transform:scale(1)", None), (T, "opacity:1", None)]))
    k.append(_kf("ha-dr2", [(0, "opacity:1;transform:scale(1)", None), (0.3, "opacity:0", None),
                            (0.8, "opacity:0;transform:scale(.35)", OUT),
                            (1.03, "opacity:1;transform:scale(1)", None),
                            (T, "opacity:1;transform:scale(1)", None)]))
    k.append(_kf("ha-ins", [(0, "opacity:1;transform:scale(1)", None), (0.3, "opacity:0", None),
                            (1.05, "opacity:0;transform:scale(.7)", OUT),
                            (1.27, "opacity:1;transform:scale(1.1)", SINE),
                            (1.55, "transform:scale(1)", None), (T, "opacity:1;transform:scale(1)", None)]))
    k.append(_kf("ha-ip", [(0, "opacity:.8;transform:scale(1)", OUT),
                           (1.0, "opacity:0;transform:scale(2)", None),
                           (T, "opacity:0;transform:scale(2)", None)]))
    # the answer at the bottom: the ripple rings, the bars breathe
    rip = [(0, "opacity:0;transform:scale(1)", None)]
    for t in (a - RIP_T0 for a in ANSWERS):
        rip += [(t, "opacity:.75;transform:scale(1)", OUT), (t + 1.2, "opacity:0;transform:scale(6.4)", None),
                (t + 1.21, "opacity:0;transform:scale(1)", None)]
    rip.append((T, "opacity:0;transform:scale(1)", None))
    k.append(_kf("ha-rip", rip))
    pop = [(0, "transform:scale(1)", None)]
    for t in (a - RIP_T0 for a in ANSWERS):
        pop += [(t, "transform:scale(1)", OUT), (t + 0.16, "transform:scale(1.3)", SINE),
                (t + 0.45, "transform:scale(1)", None)]
    pop.append((T, "transform:scale(1)", None))
    k.append(_kf("ha-rpop", pop))
    ans = [a - BAR_T0 for a in ANSWERS]
    bumps = [a - BUMP_LEAD for a in ans]
    k.append(_kf("ha-bl", _pulses([(b, 0.16) for b in bumps] + [(a, 0.12) for a in ans])))
    k.append(_kf("ha-bm", _pulses([(b, 0.05) for b in bumps] + [(a, 0.22) for a in ans])))
    k.append(_kf("ha-bh", _pulses([(ans[0], 0.12), (ans[1], 0.14), (ans[2], 0.28)])))
    # ambient, on their own clocks
    k.append("@keyframes ha-spin{to{transform:rotate(360deg)}}")
    fx, fy, fs = PUFF_FROM
    tx, ty, ts = PUFF_TO
    mx, my, ms, _ = _puff_at(0.65)
    k.append(f"@keyframes ha-puff{{0%{{opacity:0;transform:{_puff_tf(fx, fy, fs)}}}"
             f"15%{{opacity:1}}65%{{opacity:1;transform:{_puff_tf(mx, my, ms)}}}"
             f"100%{{opacity:0;transform:{_puff_tf(tx, ty, ts)}}}}}")
    pw, ph = PLANE_BOX[2], PLANE_BOX[3]
    k.append(f"@keyframes ha-glide{{to{{transform:translate({_p(3 / pw * 100)}%,{_p(-6 / ph * 100)}%) "
             "rotate(-1deg)}}")
    # the wings flex on the story's clock, both panels of both wings, the
    # tips together up and down the picture
    k += [_wing_kf("ha-" + cls[1:] + ("o" if panel else ""), wing, panel)
          for cls, wing, _ in WINGS for panel in (0, 1)]
    return "\n".join(k)


def _at_s(t, cross=False):
    """The delay of an animation whose event is at story time t: negative, so
    it starts with the story (see LEAD); positive for one whose motion runs on
    past the loop's end, so it waits at rest until its first event."""
    return f"{round(t if cross else t - T, 3)}s"


def _anim_rules():
    s = ".ha[data-live]"
    run = f"{T:g}s"
    r = [f"{s} .mq{{animation:ha-soft {run} infinite var(--d)}}",
         f"{s} .mqf{{animation-name:ha-fire}}"]
    for i, (_, t0, _, _) in enumerate(PACKETS):
        r.append(f"{s} .mpk{i}{{animation:ha-pk{i} {run} linear infinite {_at_s(t0)}}}")
    r += [f"{s} .mem{{animation:ha-emit {run} infinite {_at_s(0.42)}}}",
          f"{s} .mem2{{animation-delay:{_at_s(0.62)}}}",
          f"{s} .mhum{{animation:ha-emit {run} infinite {_at_s(8.7)}}}",
          f"{s} .mhum2{{animation-delay:{_at_s(8.92)}}}",
          f"{s} .mnp{{animation:ha-new {run} infinite {_at_s(1.3)}}}",
          f"{s} .mnh{{animation:ha-halo {run} infinite {_at_s(1.3)}}}",
          f"{s} .mfit{{animation:ha-fit {run} infinite {_at_s(1.45)}}}",
          f"{s} .mbd{{animation:ha-band {run} infinite {_at_s(1.45)}}}",
          f"{s} .hlet-b{{animation:ha-let {run} infinite {_at_s(TRAIN_T - 0.1)}}}",
          f"{s} .hwv{{animation:ha-wv {run} infinite var(--d)}}",
          f"{s} .hnl1{{animation:ha-flash {run} infinite {_at_s(6.4)}}}",
          f"{s} .hne1{{animation:ha-flash {run} infinite {_at_s(6.55)}}}",
          f"{s} .hnl2{{animation:ha-flash {run} infinite {_at_s(6.85)}}}",
          f"{s} .hne2{{animation:ha-flash {run} infinite {_at_s(7.0)}}}",
          f"{s} .hnl3{{animation:ha-flash {run} infinite {_at_s(7.31)}}}",
          f"{s} .hlet-c{{animation:ha-let-c {run} infinite {_at_s(CAR_T - 0.1)}}}"]
    for cls, name in (("mt1", "t1"), ("mdr1", "dr1"), ("mt3", "t3"), ("mdr2", "dr2"), ("mins", "ins")):
        r.append(f"{s} .{cls}{{animation:ha-{name} {run} infinite {_at_s(10.25)}}}")
    r += [f"{s} .mip{{animation:ha-ip {run} infinite {_at_s(11.3, True)}}}",
          f"{s} .mrip{{animation:ha-rip {run} infinite {_at_s(RIP_T0, True)}}}",
          f"{s} .mrgc{{animation:ha-rpop {run} infinite {_at_s(RIP_T0, True)}}}",
          f"{s} .mbl{{animation:ha-bl {run} infinite var(--d)}}",
          f"{s} .mbm{{animation:ha-bm {run} infinite var(--d)}}",
          f"{s} .mbh{{animation:ha-bh {run} infinite var(--d)}}",
          f"{s} .mrot{{animation:ha-spin 15s linear infinite}}",
          f"{s} .mpf{{animation:ha-puff {PUFF}s linear infinite calc((var(--p) + .5) * {-PUFF / 5}s)}}",
          f"{s} .mfl{{animation:ha-glide 4s {SINE} infinite alternate}}"]
    # each panel of each wing, the outer riding on the inner; between two
    # extremes the rule's easing is half a cosine (SINE_INOUT)
    ease = f"cubic-bezier({SINE_INOUT.replace(' ', ',')})"
    for cls, *_ in WINGS:
        for c in (cls, cls + "o"):
            r.append(f"{s} .{c}{{animation:ha-{c[1:]} {run} {ease} infinite {_at_s(0)}}}")
    return "\n".join(r)


def _lit_rules():
    """One lit key keeps what carries its data and brightens its path to the
    data blue; the rest steps back. Stepping back takes --t-mid, coming
    forward --t-fast, both --t-quick when the keyboard moved it."""
    keep = ",".join(f".ha[data-hl={k[0]}] .hdim[data-k~={k[0]}]" for k in KEYS)
    path = ",".join(f".ha[data-hl={k[0]}] :is(.hl,.hf)[data-k~={k[0]}]" for k in KEYS)
    return (f"{keep}{{opacity:1;transition-duration:var(--ha-up)}}\n"
            f"{path}{{stroke:var(--ha-data)}}")


def _origin(cls, box, x, y):
    """A mover's pivot: a point of the drawing, in percent of the mover's box."""
    bx, by, bw, bh = box
    return f".ha .{cls}{{transform-origin:{_p((x - bx) / bw * 100)}% {_p((y - by) / bh * 100)}%}}"


def _pivots():
    wings = []
    for cls, wing, _ in WINGS:
        root, cut = _wing(wing)[2:4]
        wings += [_origin(cls, PLANE_BOX, *root), _origin(cls + "o", PLANE_BOX, *cut)]
    return "\n".join(wings + [_origin("mfl", PLANE_BOX, *SENSORS["pl"]),
                      _origin("mbg", (0, BAR_Y, 1, BAR_H), 0.5, RIP[1]),
                      ".ha .mem,.ha .mhum{transform-origin:50% 100%}",
                      ".ha .mdr1,.ha .mdr2{transform-origin:0 0}"])


CSS = """
/* =========================== hero illustration =========================== */
/* Every colour is a token or a mix of two tokens in OKLab, at the column's
   hue. --ha-ink is the column's navy for structure, --ha-data the link blue
   for data (rings, packets, the lit tree); the tints are --link let into
   --page, stepped to the reference's lightness ladder. In dark mode the ink
   flips to the light link blue so the strong strokes stay strong. The figure
   is a size container: under 400px it draws its data a size larger. */
.ha{position:relative;margin:0;overflow:clip;max-width:none;container:ha/inline-size;
  --ha-ink:var(--nav);
  --ha-data:var(--link);
  --ha-line:color-mix(in oklab,var(--link) 72%,var(--page));
  --ha-mid:color-mix(in oklab,var(--link) 68%,var(--page));
  --ha-soft:color-mix(in oklab,var(--link) 40%,var(--page));
  --ha-hair:color-mix(in oklab,var(--link) 30%,var(--page));
  --ha-tint:color-mix(in oklab,var(--link) 19%,var(--page));
  --ha-tint2:color-mix(in oklab,var(--link) 11%,var(--page));
  --ha-pale:color-mix(in oklab,var(--link) 8%,var(--page));
  --ha-win:var(--page);
  --ha-acc:var(--accent);
  --ha-acc-soft:color-mix(in oklab,var(--accent) 16%,var(--page));
  --ha-up:var(--t-fast);--ha-down:var(--t-mid)}
.ha[data-kb]{--ha-up:var(--t-quick);--ha-down:var(--t-quick)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .ha{--ha-ink:var(--link)}}
:root[data-theme="dark"] .ha{--ha-ink:var(--link)}

.ha__stage{position:relative}
.ha__svg{position:relative;display:block;width:100%;height:auto;aspect-ratio:1260/812}
/* The layers over the drawing (heroart.py's docstring says why most parts
   that move are HTML): a layer is placed in percent of the figure, a mover
   is what the animation moves, and each holds an SVG of its part in the
   drawing's own units. None clips; the figure does, at its edge. */
.ha__fx{position:absolute;inset:0;pointer-events:none}
.ha__o{position:absolute;display:block}
.ha__m{position:absolute;display:block;inset:0}
.ha__o svg{position:absolute;display:block;width:100cqw;height:@SVGH@cqw;overflow:visible}
.ha__far{will-change:transform}
/* Paint. Bare class selectors on purpose: the reflection, the second train
   and the trace's repeats are <use> clones, and a rule that needs an ancestor
   (".ha .x") never reaches inside a clone, while a bare class does. The
   prefixes hf- (fill) and hs- (stroke) are this part's own. hns keeps a
   hairline one screen width at any size. */
.hf-n{fill:none}
.hf-i{fill:var(--ha-ink)}
.hf-m{fill:var(--ha-mid)}
.hf-s{fill:var(--ha-soft)}
.hf-t{fill:var(--ha-tint)}
.hf-t2{fill:var(--ha-tint2)}
.hf-p{fill:var(--ha-pale)}
.hf-w{fill:var(--ha-win)}
.hs-i{stroke:var(--ha-ink)}
.hs-m{stroke:var(--ha-mid)}
.hs-s{stroke:var(--ha-soft)}
.hs-h{stroke:var(--ha-hair)}
.hs-t{stroke:var(--ha-tint)}
.hns{vector-effect:non-scaling-stroke}
.ha .hgs-i{stop-color:var(--ha-ink)}
.ha .hgs-s{stop-color:var(--ha-soft)}
.ha .hgs-t{stop-color:var(--ha-tint)}
.ha .hgs-p{stop-color:var(--ha-pale)}
.ha .hgs-pg{stop-color:var(--page)}
.ha .hrefl{opacity:.62}
.ha .hpf{fill:var(--ha-tint2)}

/* links: the mesh and the climbs dashed, the model-to-model links and the
   plane's climb lighter, the faint mesh dotted; all one screen width */
.ha .hl,.ha .hf{fill:none;vector-effect:non-scaling-stroke;
  transition:stroke var(--ha-up) var(--ease-state)}
.ha .hl{stroke:var(--ha-line);stroke-width:.8px;stroke-dasharray:2.2px 1.8px}
.ha .hl2{stroke:var(--ha-hair);stroke-width:.6px}
.ha .hf{stroke:var(--ha-hair);stroke-width:.75px;stroke-dasharray:0 2.4px;stroke-linecap:round}
.ha .hdot{fill:var(--ha-mid)}

/* sensors: a paper-white ring in the link blue on a pale halo */
.ha .hhalo{fill:var(--ha-pale);stroke:var(--ha-hair);stroke-width:.8}
.ha .hrg{fill:var(--ha-win);stroke:var(--ha-data);stroke-width:2.4}
.ha .hq{fill:none;stroke:var(--ha-data);stroke-width:2.2}

/* the moving parts at rest: pulses, packets, emitters and the ripple hidden,
   the network's flashes and the hanger wave hidden, the answers shown */
.ha .mq,.ha .mpk,.ha .mem,.ha .mhum,.ha .mrip,.ha .mip{opacity:0}
.ha .hpg{fill:var(--ha-data);fill-opacity:.28}
.ha .hpd{fill:var(--ha-data)}
.ha .hwv{fill:none;stroke:var(--ha-ink);stroke-width:2;opacity:0}
.ha .hnl{fill:var(--ha-data);fill-opacity:.22;opacity:0}
.ha .hne{fill:none;stroke:var(--ha-data);stroke-width:1.8;stroke-opacity:.55;opacity:0}
.ha .hlit{fill:none;stroke:var(--ha-data);stroke-width:2.6;stroke-linejoin:round}
.ha .hac{fill:var(--ha-acc)}
.ha .hah{fill:var(--ha-acc-soft);stroke:var(--ha-acc);stroke-opacity:.35;stroke-width:1}
.ha .hip{fill:none;stroke:var(--ha-acc);stroke-width:1.6}
""" + _pivots() + """

/* ---------------------------------------------------------------- keys */
/* Thirteen transparent buttons over the drawing, one toolbar with one tab
   stop. They show only once the script runs: without it they would do
   nothing. No box: a lit key keeps its structure and its path and lets the
   rest step back; keyboard focus adds one short rule under the structure. */
.ha__keys{position:absolute;inset:0}
.ha__key{position:absolute;display:block;min-width:24px;min-height:24px;margin:0;padding:0;
  border:0;border-radius:var(--r-md);background:none;color:inherit;font:inherit;
  transform:translate(-50%,-50%);cursor:pointer;-webkit-tap-highlight-color:transparent}
.ha__key:focus,.ha__key:focus-visible{outline:none}
.ha__key:focus-visible::after{content:"";position:absolute;left:50%;top:100%;width:20px;height:2px;
  margin:6px 0 0 -10px;border-radius:1px;background:var(--focus)}
.ha__key[data-key=car]{z-index:1}
.ha__sr{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;
  clip-path:inset(50%);white-space:nowrap;border:0}

/* one key lit: what carries its data stays and its path brightens, the rest
   steps back */
.ha .hdim{transition:opacity var(--ha-up) var(--ease-state)}
.ha[data-hl] .hdim{opacity:.34;transition-duration:var(--ha-down)}
""" + _lit_rules() + """

/* one quiet line under the drawing names the pair while one is lit; its
   height is kept at all times, so nothing below it moves */
.ha__read{display:flex;align-items:center;gap:6px;min-height:21px;margin:10px 0 0;
  font:400 14px/1.5 var(--sans);letter-spacing:.01em;color:var(--muted);
  opacity:0;transition:opacity var(--ha-up) var(--ease-state)}
.ha[data-hl] .ha__read{opacity:1;transition-duration:var(--ha-down)}
.ha__a{color:var(--body)}
.ha__arr{flex:none;display:block}

/* ------------------------------------------------------------ narrow */
/* A phone draws the figure about 350px wide. The dotted links fall under a
   hairline and go; rings and packets grow by radius (not by transform, so
   nothing leaves its centre); the trace gains weight (a bare class, to
   reach its repeats, which are <use> clones). */
@container ha (max-width:400px){
  .ha .hf{display:none}
  .ha .hl{stroke-width:1px}
  .ha .hfire .hrg,.ha .hsoft .hrg,.ha .hq{r:7px}
  .ha .hfire .hhalo,.ha .hsoft .hhalo{r:12.5px}
  .ha .hrg{stroke-width:3}
  .ha .hpd{r:6px}
  .ha .hpg{r:11px}
  .htr{stroke-width:2.4}
}

@media (prefers-reduced-motion:no-preference){
""" + _motion_css() + "\n" + _anim_rules() + """
}
/* paused off screen and in a hidden tab, never by the reader */
.ha:not([data-run]) *{animation-play-state:paused!important}
@media (forced-colors:active){
  .ha__key:focus-visible{outline:2px solid Highlight;outline-offset:2px}
  .ha__key:focus-visible::after{display:none}
}
@media print{.ha *{animation:none!important}.ha__keys,.ha__read{display:none}}
"""
CSS = CSS.replace("@SVGH@", _p(VB[3] / VB[2] * 100))

JS = """
var fig=document.querySelector('.ha');
if(!fig||fig.haReady)return;
fig.haReady=true;
var stage=fig.querySelector('.ha__stage'),bar=fig.querySelector('.ha__keys'),
  ra=fig.querySelector('.ha__a'),rb=fig.querySelector('.ha__b'),
  far=fig.querySelector('.ha__far'),ks=[].slice.call(bar.querySelectorAll('.ha__key')),
  svg=fig.querySelector('.ha__svg'),vib=document.getElementById('ha_vib'),
  RM=matchMedia('(prefers-reduced-motion: reduce)'),
  FINE=matchMedia('(hover: hover) and (pointer: fine)'),
  seen=false,live=false,lead=0,t0=-1,tq=0;
/* ---- the far hills drift against the pointer on a critically damped spring
   (response .6 s): a mouse only, motion allowed, while the figure runs. The
   far layer is its own compositor layer, so a step moves it without a paint;
   the drift is in drawing units, @W@ of them across the layer */
var px=0,pv=0,pt=0,raf=0,last=0;
function step(t){
  var dt=Math.min(.05,last?(t-last)/1000:.016),w=10.47;last=t;
  pv+=(w*w*(pt-px)-2*w*pv)*dt;px+=pv*dt;
  if(Math.abs(pt-px)<.01&&Math.abs(pv)<.01){px=pt;pv=0;raf=0;last=0}
  far.style.transform=px?'translateX('+(px/@W@*100).toFixed(3)+'%)':'';
  if(raf)raf=requestAnimationFrame(step);
}
function aim(to){pt=to;if(!raf&&px!==pt){last=0;raf=requestAnimationFrame(step)}}
function still(){if(raf)cancelAnimationFrame(raf);raf=0;px=pv=pt=0;far.style.transform=''}
stage.addEventListener('pointermove',function(e){
  if(e.pointerType!=='mouse'||!FINE.matches||!fig.hasAttribute('data-run'))return;
  var r=stage.getBoundingClientRect();aim(((e.clientX-r.left)/r.width-.5)*-18)});
stage.addEventListener('pointerleave',function(){aim(0)});
/* ---- the tall building and the bridge vibrate, and the train, the car and
   the trace travel, by SMIL on the drawing's own clock ("the vibration" and
   "the travellers" say why). One animation leads and the rest begin
   with it: the script begins it once, with the story, at t0 on that clock, and
   from then on only pauses, resumes and seeks the clock. Its loop begins at
   rest, so seeking to t0 restarts it with the story, or holds it still when
   motion is not wanted and while printing (an animation ended and begun
   again does not restart alike in every browser) */
function shake(){if(!vib)return;if(t0<0){vib.beginElement();t0=svg.getCurrentTime()}else svg.setCurrentTime(t0)}
function rest(){if(t0>=0){svg.pauseAnimations();svg.setCurrentTime(t0)}}
/* ---- running: seen, in a visible tab, motion allowed. Nothing the reader
   does holds it: it pauses only where no one can see it, which spares the
   phone the work. The story starts @L@ ms after the figure is first seen, all
   at once, and loops for as long as it runs */
function sync(){
  if(RM.matches){
    live=false;still();clearTimeout(lead);lead=0;rest();
    fig.removeAttribute('data-live');fig.removeAttribute('data-run');return;
  }
  var run=seen&&!document.hidden;
  if(run&&!live&&!lead)lead=setTimeout(function(){lead=0;live=true;fig.setAttribute('data-live','');shake();sync()},@L@);
  if(run&&live){fig.setAttribute('data-run','');svg.unpauseAnimations()}
  else{fig.removeAttribute('data-run');svg.pauseAnimations();aim(0)}
}
/* print shows the picture at rest, as the stylesheet does for the rest of the
   story, then the SMIL goes on from where it was (tq keeps where: tp below is
   the latest pin's turn) */
addEventListener('beforeprint',function(){if(t0>=0){tq=svg.getCurrentTime();rest()}});
addEventListener('afterprint',function(){if(t0>=0){svg.setCurrentTime(tq);sync()}});
/* ---- the keys: the latest input wins (a pointer that rests, a key the
   keyboard reached, a pin). A pin lights a pair and keeps it lit until the
   next press; the story runs on under it. A pointer waits 90 ms before it
   lights and 90 ms before it lets go, so sliding from one structure to the
   next never flashes the whole picture back */
var cur=null,hov=null,foc=null,pin=null,th=0,tf=0,tp=0,n=0,intent=0,grace=0;
function pick(){var k=null,t=0;
  if(hov&&th>t){k=hov;t=th}if(foc&&tf>t){k=foc;t=tf}if(pin&&tp>t){k=pin;t=tp}return k}
function key(k){for(var i=0;i<ks.length;i++)if(ks[i].getAttribute('data-key')===k)return ks[i]}
function show(kb){
  var k=pick();clearTimeout(grace);
  if(kb)fig.setAttribute('data-kb','');else fig.removeAttribute('data-kb');
  if(k===cur)return;cur=k;
  if(!k){fig.removeAttribute('data-hl');return}
  var b=key(k),to=b.getAttribute('data-to');
  ra.textContent=to?b.textContent:b.getAttribute('data-n')+' structures';
  rb.textContent=to?key(to).textContent:b.textContent;
  fig.setAttribute('data-hl',k);
}
function press(){ks.forEach(function(b){
  b.setAttribute('aria-pressed',b.getAttribute('data-key')===pin?'true':'false')})}
function rove(i){ks.forEach(function(b,j){b.tabIndex=j===i?0:-1})}
ks.forEach(function(b,i){
  var k=b.getAttribute('data-key');
  b.addEventListener('pointerenter',function(e){
    if(e.pointerType==='touch')return;
    clearTimeout(grace);clearTimeout(intent);
    intent=setTimeout(function(){hov=k;th=++n;show(false)},90);
  });
  b.addEventListener('pointerleave',function(e){
    if(e.pointerType==='touch')return;
    clearTimeout(intent);
    if(hov!==k)return;
    hov=null;grace=setTimeout(function(){show(false)},90);
  });
  b.addEventListener('focus',function(){
    var v=true;try{v=b.matches(':focus-visible')}catch(x){}
    rove(i);if(v){foc=k;tf=++n;show(true)}
  });
  b.addEventListener('blur',function(){if(foc===k){foc=null;show(true)}});
  b.addEventListener('click',function(e){pin=pin===k?null:k;tp=++n;press();show(!e.detail)});
});
bar.addEventListener('keydown',function(e){
  var i=ks.indexOf(document.activeElement),m=ks.length,j;
  if(i<0)return;
  switch(e.key){
    case'ArrowRight':case'ArrowDown':j=(i+1)%m;break;
    case'ArrowLeft':case'ArrowUp':j=(i+m-1)%m;break;
    case'Home':j=0;break;
    case'End':j=m-1;break;
    case'Escape':if(pin){pin=null;tp=++n;press();show(true);e.preventDefault()}return;
    default:return;
  }
  e.preventDefault();ks[j].focus();
});
document.addEventListener('pointerdown',function(e){
  if(pin&&!(e.target.closest&&e.target.closest('.ha__key'))){pin=null;tp=++n;press();show(false)}
});
bar.hidden=false;
/* ---- on screen. No IntersectionObserver: while one holds a target, Chrome
   gives the page a main-thread frame at every vsync for as long as anything
   on it animates (the masthead above a phone's fold, measured at 59 style
   recalculations a second while the figure waited below it). The figure is
   looked at instead, once a frame at most, when the page scrolls or resizes,
   when the fonts arrive and when the page has loaded */
var look=0;
function check(){
  look=0;var r=fig.getBoundingClientRect(),on=r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth;
  if(on!==seen){seen=on;sync()}
}
function soon(){if(!look)look=requestAnimationFrame(check)}
addEventListener('scroll',soon,{passive:true});
addEventListener('resize',soon);
addEventListener('load',soon);
addEventListener('pageshow',soon);
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(soon);
soon();
document.addEventListener('visibilitychange',sync);
if(RM.addEventListener)RM.addEventListener('change',sync);else if(RM.addListener)RM.addListener(sync);
sync();
""".replace("@L@", str(round(LEAD * 1000))).replace("@W@", _n(FAR_BOX[2]))
