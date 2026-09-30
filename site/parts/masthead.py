# -*- coding: utf-8 -*-
"""masthead: the band across the top of the home page.

His sentence on waves and data, set as his slides 1 and 4 set it: light
words on the deepest navy, one centred block. Under it the sentence is told
again as a figure, in the order of his words, each part drawn from a model
and computed exactly (29 Sep 2026, the client: an app-like animation in the
LaTeX and manim style; then "very stylish, clear and beautiful"):

1. "elastic waves causing dynamic vibrations in a bridge": a cable-stayed
   bridge in fine line art (spans 150 + 350 + 150 m, two pylons, a fan of
   stays). It is built as one is built: the pylons rise, the deck grows out
   from both of them at once (balanced cantilevers), each stay taking its
   segment as the front passes, the side spans land on their abutments and
   the main span closes at its middle. Then the finished deck swings in its
   first vertical mode, computed here (_deck_mode(): the deck a beam on the
   stays' springs, by finite differences), at its own frequency, 0.46 Hz, in
   real time.
2. "the matter waves inside a single atom": the point where the deck closed
   is taken out as a lens (TikZ's spy), and in it an atom: its nucleus, the
   Bohr orbit and the de Broglie wave standing on it, five wavelengths round
   (2 pi r = 5 lambda).
3. "wave motion sits at the center of the physical world": the wave leaves
   the atom and runs on through the middle of the band, drifting right.
4. "arrives as discrete measurements": samples drop onto it, a stem and a
   point every T, and the line fades, leaving only the numbers.
5. "Data analytics is how we recover the information": each sample's sinc
   rises and their sum, the Whittaker-Shannon series of the very samples on
   the page, draws the recovered wave through them in the band's one warm
   mark, a light crimson (no orange: the client disliked it in animations).

Where the story is. One stage is told at a time, at full strength, and his
phrase for it is lit in step. A stage not yet told is not drawn; a stage
told steps back to 38%, so the eye is always on the one being told. A pen
point, white with a soft light of its line's colour, rides the head of
every stroke that is being drawn (the deck's four fronts, the orbit, the
wave, the recovery), so the eye has one place to follow. At the end every
stage comes forward again, left to right, and the figure comes to rest.

The formulas. Each stage's formula is set in Computer Modern by
site/mathtex.py (MathML in Site Math, Latin Modern Math) over its stage, in
a row of its own on one baseline, 15px (14px in a band under 380px), no
stroke ever crossing a label. The row is laid out as two pairs about the
wave at the centre, the physical world (the bridge, the atom) and the data
(the samples, the recovery); the samples' stretch is sized so the space
inside the right pair equals the space inside the left one, while each
formula keeps 12px either side over its stretch and the wave at least a
wavelength and a quarter. A one-row strip too narrow for that sets the
data's two short (x[n], x-hat(t)). A formula arrives on the spring, out of
a 3px blur, and steps back with its stage.

Motion. The story takes 9 s; its first stroke is on screen at 0.3 s.
Strokes draw along their length with manim's smooth (seg); things that
arrive settle on Motion's spring (settle(): motion.dev's spring with bounce
0, in closed form). The figure then rests as a composed final figure, the
same one a reader who asked for less motion is shown at once: the deck held
at the top of its swing, the moment its speed is zero (so it stops the way a
swing turns), the orbit's wave at its fullest, the drift eased to a stop.
There is no idle loop: after the story the canvas is drawn only for the
pointer. Every frame is a pure function of the clock, the
formulas and his lit phrases included, so any moment can be drawn
(band.__mh.at(t)). The story is told on every visit; back on the page by the
browser's history, the figure is already whole.

A phone. A band under 640px tells the story in two rows, one for each half
of his sentence: the physical world (the bridge, the atom, the wave running
off the row's end) and the data (the same wave's samples, from the next
row's start, and their recovery), so each part is drawn at twice the size a
single squeezed row allows, and every formula whole. The wave keeps one
phase across the break.

The pointer is a probe. Over the figure it reads the stage under it: a point
in a ring where the pointer samples it (on the deck, on the matter wave at
the pointer's angle round the nucleus, on the wave, on the nearest sample,
on the recovered wave), with a stem from the axis where the value is a
height; that stage comes forward, the others step back, and its phrase
lights. Over his sentence it works the other way: a phrase under the pointer
brings its stage forward. A tap does the same on a touch screen. Once the
story is told, the stage under the pointer lives: the deck swings on in its
mode (the ring riding it, a sensor on the deck) and the orbit's wave breathes;
let go, each runs on to the end of its period, which is its pose in the
still figure, and stops there, so the clock stops too.

The canvas is drawn only while something moves: never off screen, in a
hidden tab, or for a reader who asked for less motion. It is at most 2
device pixels per CSS pixel, and its hairlines are one device pixel, set on
the pixel grid. There is no IntersectionObserver (round-4 finding RM-3): a
passive scroll listener looks, once a frame at most. Without JavaScript the
band is his sentence alone (the strip needs the script, and shows only where
the page has it: html.js).

build.py's shell() opens <main> with the band, in <div class="mastrow">, and
theme.py places it (THE MASTHEAD). This module draws its inside only, so its
root is a plain <div>. Every selector sits under .masthead (the strip also
reads html.js), every colour is a theme token but the figure's two inks on
the navy, --mh-sky and --mh-rose, which the band defines for itself and
whose contrast is measured in tests/test_masthead.py; no :root variable is
written. His words go into the page exactly as given.
"""

import json
import math
import re

import mathtex

__all__ = ["CSS", "JS", "render"]

# ------------------------------------------------------------------ the strip
STRIP = 1100        # px: the strip is never wider than the sentence above it
HIGH = (66, 128)    # px: the strip's height, in one row, and in two on a phone
ROW2 = 76           # px: the second row's top, on a phone
AXIS = (44, 38)     # px below a row's top: the axis of the physical row (the deck,
                    # the atom's centre, the wave) and of the data row, on a phone
BASE = 15           # px below a row's top: the baseline all the formulas stand on
TWO = 640           # px: a band narrower than this tells the story in two rows
SMALL = 380         # px: a band narrower than this sets its formulas at 14px, not 15
INSET = 7           # px: the strip's inset, room for the abutments' supports and their ground
LW = (1.5, 1.5, 1.75)   # px: the waves, the pylons, the recovered wave

# ------------------------------------------------------------------ the bridge
# A three-span cable-stayed bridge, its deck a steel box girder carried by
# two fans of stays. The deck is a beam, EI v'''' = w^2 m v, pinned at the
# abutments, resting on the pylons' crossbeams and hung from each stay as
# from a spring of vertical stiffness E A sin^2(a) / L. Each stay's area is
# what carries its share of the deck's weight at a stay's working stress.
# The pylons are taken as rigid. Solved by finite differences every NODE
# metres (a banded Cholesky and inverse iteration, in plain Python, a few
# milliseconds); tests/test_masthead.py checks it against a closed form and
# against a Rayleigh-Ritz solution of the same model.
SIDE, MAIN = 150.0, 350.0         # m: side spans and main span
SPAN = 2 * SIDE + MAIN            # m: 650
PYLONS = (SIDE, SIDE + MAIN)      # m along the deck
TOWER = 100.0                     # m: a pylon's height above the deck
PIER = 45.0                       # m: the deck above the pier's footing
EI = 4.0e11                       # N m^2: the deck's bending stiffness
MASS = 18000.0                    # kg/m: the deck's mass
E_STAY = 195e9                    # Pa: a stay's modulus
WORKING = 0.45 * 1860e6           # Pa: a stay's stress under the deck's weight
GRAV = 9.81                       # m/s^2
PITCH = 20.0                      # m between two stays' deck anchors
MAIN_STAYS, SIDE_STAYS = 8, 7     # stays per pylon into the main span, into the side span
ANCHOR = (60.0, 95.0)             # m above the deck: the nearest stay's pylon anchor, the farthest's
NODE = 5.0                        # m between two nodes


def _stays():
    """Each stay: (deck anchor s, pylon s, anchor height h, vertical stiffness, rank),
    s in metres along the deck, rank 0 for the stay nearest its pylon."""
    out = []
    far = max(MAIN_STAYS, SIDE_STAYS)
    for pylon, main in ((PYLONS[0], 1), (PYLONS[1], -1)):
        for count, way in ((MAIN_STAYS, main), (SIDE_STAYS, -main)):
            for k in range(1, count + 1):
                d = k * PITCH
                h = ANCHOR[0] + (ANCHOR[1] - ANCHOR[0]) * (k - 1) / (far - 1)
                chord = math.hypot(d, h)
                sin = h / chord
                area = MASS * GRAV * PITCH / (sin * WORKING)
                out.append((pylon + way * d, pylon, h, E_STAY * area * sin * sin / chord, k - 1))
    return out


STAYS = _stays()


def _deck_mode(stays=STAYS, rests=PYLONS):
    """The deck's first vertical mode: (frequency in Hz, shape at every node,
    the largest swing 1, the main span's middle moving up). The deck hangs
    from `stays` and rests on the pylons at `rests` (without either it is a
    simply supported beam, which the tests hold to its closed form)."""
    n = int(round(SPAN / NODE))
    c = EI / NODE ** 4
    spring = [0.0] * (n + 1)
    for s, _, _, k, _ in stays:
        spring[int(round(s / NODE))] += k / NODE
    fixed = {0, n} | {int(round(p / NODE)) for p in rests}
    free = [i for i in range(n + 1) if i not in fixed]
    size = len(free)

    def entry(i, j):
        # the five-point fourth difference; a pinned end reflects its
        # neighbour (v(-h) = -v(h)), so the first and last free rows lose c
        d = j - i
        if d == 0:
            return 6 * c + spring[i] - (c if i in (1, n - 1) else 0)
        return -4 * c if d == 1 else c if d == 2 else 0.0

    band = [[entry(free[j], free[j + k]) if j + k < size and free[j + k] - free[j] <= 2 else 0.0
             for k in range(3)] for j in range(size)]
    low = [[0.0] * 3 for _ in range(size)]     # low[j][k] = L[j][j - k], K = L L^T
    for j in range(size):
        for k in (2, 1):
            i = j - k
            if i < 0:
                continue
            acc = band[i][k]
            for p in range(max(0, j - 2), i):
                acc -= low[j][j - p] * low[i][i - p]
            low[j][k] = acc / low[i][0]
        low[j][0] = math.sqrt(band[j][0] - low[j][1] ** 2 - low[j][2] ** 2)

    def solve(b):
        y = [0.0] * size
        for j in range(size):
            acc = b[j]
            for k in (1, 2):
                if j - k >= 0:
                    acc -= low[j][k] * y[j - k]
            y[j] = acc / low[j][0]
        x = [0.0] * size
        for j in range(size - 1, -1, -1):
            acc = y[j]
            for k in (1, 2):
                if j + k < size:
                    acc -= low[j + k][k] * x[j + k]
            x[j] = acc / low[j][0]
        return x

    # inverse iteration, from a half sine over the whole deck
    v = [math.sin(math.pi * free[j] / n) for j in range(size)]
    for _ in range(300):
        w = solve(v)
        norm = math.sqrt(sum(x * x for x in w))
        w = [x / norm for x in w]
        if sum((a - b) ** 2 for a, b in zip(w, v)) < 1e-26:
            v = w
            break
        v = w
    kv = [band[j][0] * v[j] for j in range(size)]
    for j in range(size):
        for k in (1, 2):
            if j + k < size:
                kv[j] += band[j][k] * v[j + k]
                kv[j + k] += band[j][k] * v[j]
    omega2 = sum(a * b for a, b in zip(v, kv)) / (MASS * sum(a * a for a in v))
    shape = [0.0] * (n + 1)
    for j, i in enumerate(free):
        shape[i] = v[j]
    top = max(abs(x) for x in shape)
    sign = 1 if shape[n // 2] > 0 else -1
    return math.sqrt(omega2) / (2 * math.pi), [sign * x / top for x in shape]


F1, SHAPE = _deck_mode()          # 0.462 Hz: a swing every 2.16 s, drawn in real time

# ------------------------------------------------------------------ the atom
QUANTUM = 5         # n: the orbit carries five wavelengths, 2 pi r = 5 lambda
LENS = (20, 18)     # px: the lens's radius, one row and two
ORBIT = 0.6         # the orbit's radius, of the lens's
RIPPLE = 0.16       # the matter wave's amplitude, of the lens's radius
ATOM_PERIOD = 2.4   # s: one breath of the standing wave (slowed, as any atom's must be)

# ------------------------------------------------------------------ the signal
# The wave the atom sends on, sampled and recovered. Everything is measured
# along the signal from its far end (the strip's right end, or on a phone
# the second row's), so the wave, the samples and the recovered wave keep
# one phase at any width, and across a phone's two rows: a sample u px from
# the end sits where the wave is at u. The recovery is the Whittaker-Shannon
# series of the samples themselves, those on the page and, beyond the end,
# the ones the page does not show (VIRTUAL of them), since the signal goes
# on: at the end of the strip it is then within 0.1px of the wave.
LAMBDA = ((112, 160, 0.146), (80, 128, 0.231))   # px: wavelength, one row and two:
                    # at least, at most, and its share of the strip's width between
AMP = (9, 7)        # px: amplitude
PERIOD = 6          # s per wavelength while it drifts: 26.7px a second in one row
PER_WAVE = 8        # samples per wavelength: T = lambda / 8, four times the Nyquist rate's
VIRTUAL = 64        # samples summed beyond the signal's end
PHASE_END = 0.0     # the wave's phase, in wavelengths, when it has come to rest

# The formulas' widths at 15px in Latin Modern Math, measured in Chromium:
# u(x,t), 2 pi r = 5 lambda, x[n] = x(nT) or x[n], and the recovery's whole or x-hat(t).
TAG_W = ((41, 59.5, 86, 190), (41, 59.5, 29, 30))

# ------------------------------------------------------------------ the story
# When each stage starts (s), in the order of his sentence; when every stage
# comes forward again; when the figure is still. The deck's fronts leave the
# pylons CANT[0] after the first stage starts and close CANT[1] later; each
# formula arrives TAG_AT after its stage starts.
STAGES = (0.3, 1.78, 3.25, 4.6, 6.05)
SWEEP = 7.85
END = 9.0
CANT = (0.32, 0.95)
CLOSE = STAGES[0] + CANT[0] + CANT[1]    # the main span closes: 1.57 s
SWING = CLOSE + 0.05                     # and the finished deck starts to swing
BREATH = STAGES[1] + 0.85                # the matter wave stands on the orbit
TAG_AT = (CLOSE - STAGES[0] + 0.03, 0.85, 0.5, 0.6)
TAG_STAGE = (0, 1, 3, 4)
DECEL = 1.0         # s: the drift comes to rest over this, from SWEEP
DIM = 0.38          # a told stage steps back to this, while the next is told
HOVER_DIM = 0.32    # the stages the pointer is not on, while it probes one
LEVELS = 6          # steps in which a phrase lights and goes out


def _turn(start, period, after, quarter):
    """The first moment after `after` at which sin(2 pi (t - start) / period)
    turns (its speed zero) at the quarter given: 0.25 for its +1, 0.75 for
    its -1, 0 for a cosine's either end (then period is half the cosine's)."""
    k = math.ceil((after - start) / period - quarter)
    return start + (k + quarter) * period


# The figure comes to rest at the top of a swing, the moment its speed is
# zero: the deck sagging (a positive sine moves it down the canvas) the first
# time it turns after the sweep has begun, the orbit's wave at its fullest.
FREEZE = (round(_turn(SWING, 1 / F1, SWEEP + 0.3, 0.25), 4),
          round(_turn(BREATH, ATOM_PERIOD / 2, SWEEP + 0.3, 0), 4))
PHASE0 = PHASE_END - ((SWEEP - STAGES[2]) + DECEL / 3) / PERIOD

# His phrases, in his words, each lit while its stage is told; the last three
# keep a mark (the highlights' names) once their stage has come.
WORDS = ("elastic waves causing dynamic vibrations in a bridge",
         "matter waves inside a single atom", "wave motion", "discrete measurements",
         "Data analytics")
MARKS = (None, None, "masthead-wave", "masthead-dots", "masthead-data")


def _seg_inverse(y):
    """When manim's smooth reaches y: the inverse of seg() in the script."""
    return (y / 4) ** (1 / 3) if y < 0.5 else 1 - (2 * (1 - y)) ** (1 / 3) / 2


STILL = END

DATA = {
    "H": list(HIGH), "row2": ROW2, "axis": list(AXIS), "base": BASE,
    "bx": INSET, "lw": list(LW), "dot": 1.9,
    # the bridge: its width in px (at least, at most, share of a one-row strip, of a phone's row)
    "bw": [76, 262, 0.235, 0.56], "span": SPAN, "node": NODE, "half": MAIN / 2, "side": SIDE,
    "shape": [round(v, 3) for v in SHAPE], "f1": round(F1, 5),
    "mid": int(round((SIDE + MAIN / 2) / NODE)),
    "pyl": list(PYLONS), "tower": TOWER, "pier": PIER,
    # each stay: deck anchor, pylon, anchor height (m), and when the deck's front passes it
    "stays": [[s, p, round(h, 2), round(_seg_inverse(abs(s - p) / (MAIN / 2)), 6)]
              for s, p, h, _, _ in STAYS],
    "bAmp": [2, 4, 10],             # the deck's swing in px: at least, at most, per px a metre
    "cant": list(CANT), "swing": round(SWING, 4), "frz": list(FREEZE),
    # the atom
    "lens": list(LENS), "gapA": [22, 14], "orbit": ORBIT, "ripple": RIPPLE,
    "quantum": QUANTUM, "atomP": ATOM_PERIOD, "spyR": 4.5, "nucleus": 2, "breath": round(BREATH, 4),
    # the signal
    "lam": [list(v) for v in LAMBDA], "amp": list(AMP), "P": PERIOD, "perWave": PER_WAVE,
    "virt": VIRTUAL, "ph0": round(PHASE0, 6), "dec": DECEL,
    # one row: the recovery's share of the samples, the fewest samples alone and
    # recovered, the fewest wavelengths the wave keeps, the room a formula keeps
    # on each side over its stretch; a phone: the recovery's share of its row
    "recShare": 0.615, "minZ": [4, 6], "minWave": 1.25, "pad": 12, "share2": 0.66,
    "tw": [list(w) for w in TAG_W], "tagGap": 16,
    "wdur": [1.4, 1.0], "rdur": 1.2,
    # the story
    "st": list(STAGES), "sweep": SWEEP, "end": END, "dim": DIM, "hovDim": HOVER_DIM,
    "tagAt": [round(STAGES[s] + a, 4) for s, a in zip(TAG_STAGE, TAG_AT)],
    "tagStage": list(TAG_STAGE), "levels": LEVELS,
    "words": list(WORDS), "marks": list(MARKS),
}

# ------------------------------------------------------------------ the formulas
# Set by site/mathtex.py, which stops the build on TeX it cannot set or a
# glyph Site Math lacks. A formula's parts take the colours of what they name,
# as manim colours a formula by its objects: the deck's u in the wave's blue,
# the samples x[n] white as their points, the recovered x-hat crimson as its
# wave. Each part is a run of the formula's top-level MathML children.
TAGS = (
    # key, TeX, [(first child, last child + 1, class)], long (wide strip only) or short
    (0, r"u(x,t)", [(0, 6, "mh-sky")], ""),
    (1, r"2\pi r=5\lambda", [(6, 7, "mh-sky")], ""),
    (2, r"x[n]=x(nT)", [(0, 4, "mh-ink")], "long"),
    (2, r"x[n]", [(0, 4, "mh-ink")], "short"),
    (3, r"\hat{x}(t)=\sum_n x[n]\,\operatorname{sinc}(t/T-n)",
     [(0, 4, "mh-rose"), (6, 10, "mh-ink")], "long"),
    (3, r"\hat{x}(t)", [(0, 4, "mh-rose")], "short"),
)


def _kids(inner):
    """The top-level elements of a run of MathML, each as its markup."""
    out, depth, start = [], 0, 0
    for m in re.finditer(r"<(/?)([a-z]+)\b[^>]*?(/?)>", inner):
        closing, empty = m.group(1) == "/", m.group(3) == "/"
        if not closing and depth == 0:
            start = m.start()
        if empty:
            if depth == 0:
                out.append(inner[start:m.end()])
            continue
        depth += -1 if closing else 1
        if closing and depth == 0:
            out.append(inner[start:m.end()])
    return out


def _formula(tex, runs):
    """One formula as a <math>, whole (mathtex splits a long inline one for
    line breaking; this one never breaks), its runs coloured."""
    out = mathtex.mathml(tex, where=f"parts/masthead.py: {tex}")
    whole = re.search(r'<span class="im-sr">(<math.*?</math>)</span>', out, re.S)
    out = whole.group(1) if whole else out
    head, inner = re.match(r"(<math[^>]*>)(.*)</math>$", out, re.S).groups()
    kids = _kids(inner)
    if "".join(kids) != inner:
        raise ValueError(f"parts/masthead.py: {tex}: unexpected MathML")
    for a, b, cls in sorted(runs, reverse=True):
        kids[a:b] = [f'<mrow class="{cls}">' + "".join(kids[a:b]) + "</mrow>"]
    return head + "".join(kids) + "</math>"


def _tags():
    out = []
    for key, tex, runs, length in TAGS:
        cls = "masthead__tex" + (f" masthead__tex--{length}" if length else "")
        out.append(f'<span class="{cls}" data-k="{key}">{_formula(tex, runs)}</span>')
    return "".join(out)


_WAVE = ('<div class="masthead__wave" aria-hidden="true">'
         '<canvas class="masthead__cv"></canvas>' + _tags() + '</div>')


def _lit():
    """His phrase while its stage is told, or probed, in LEVELS steps so it
    fades in and out: from the sentence's own ink to full white with a soft
    light of the wave's blue ("Data analytics": its crimson, lit brighter)."""
    out = []
    for i in range(1, LEVELS + 1):
        f = i / LEVELS
        blur = f"0 0 {6 + 4 * f:.1f}px"
        out.append(f"::highlight(masthead-lit{i}){{color:color-mix(in oklab,var(--nav-ink) "
                   f"{88 + 12 * f:.0f}%,var(--nav-deep));text-shadow:{blur} "
                   f"color-mix(in oklab,var(--mh-sky) {62 * f:.0f}%,transparent)}}")
        out.append(f"::highlight(masthead-litd{i}){{color:var(--mh-rose);text-shadow:{blur} "
                   f"color-mix(in oklab,var(--mh-rose) {62 * f:.0f}%,transparent)}}")
    return "\n".join(out)


CSS = """
/* ============================== masthead ============================== */
/* The deepest navy of the column's family, as his slide 1 sets the band a
   step darker than the column beside it. White on it is 17.25:1. The band is
   its own size container, so its type and spacing follow the band, not the
   window. The figure's two inks on the navy are the band's own: --mh-sky,
   the waves' blue (9.31:1 on the band, in both themes), and --mh-rose, a
   light crimson at the hue of the figures' crimson #A7203A (oklch hue 16)
   with the lightness and chroma of the orange it replaces, the recovered
   wave's and "Data analytics"'s (6.53:1; as text it needs 4.5:1). */
.masthead{container:masthead/inline-size;position:relative;display:flex;
  flex-direction:column;justify-content:center;
  background:var(--nav-deep);color:var(--nav-ink);-webkit-font-smoothing:antialiased;
  --mh-sky:#95C3EF;--mh-rose:#EF7D86}
/* the band's margins: 20px over his first line, 20px under the figure,
   whose lowest strokes stand a pixel or two above the strip's foot, so the
   block sits in the middle of the navy (measured: 23px of navy over the
   first ink, 21.5px under the last) */
.masthead__in{padding:20px clamp(20px,2.6cqi,44px) 20px}

/* His sentence: the serif, his voice, centred and balanced as the slide
   centres it, in three long lines: 17.5px in a band 1190px wide (a window of
   1440), 16px at the narrowest, on the band's width (cqi) between, in a box
   1100px wide. Lining figures, so "7 x 10^27" reads as the quantity it is.
   The words are taken 12% toward the navy (13:1 on it), so the phrases the
   figure tells can be lit in full white. While Source Serif 4 loads, Georgia
   stands in, sized to it (103%, the measured ratio of the two faces over his
   sentence), so the lines land where the font sets them. */
@font-face{font-family:"Masthead Serif Fallback";font-style:normal;font-weight:400;
  src:local("Georgia");size-adjust:103%}
.masthead__text{margin:0 auto;max-width:@STRIP@px;font:400 clamp(16px,1.47cqi,17.5px)/1.55 var(--serif);
  font-family:"Source Serif 4","Masthead Serif Fallback",var(--serif);
  letter-spacing:-.003em;text-align:center;text-wrap:balance;
  font-variant-numeric:lining-nums proportional-nums;
  color:color-mix(in oklab,var(--nav-ink) 88%,var(--nav-deep));
  text-underline-offset:.34em;text-decoration-skip-ink:none}
/* the marks, in the figure's terms (the script sets the ranges): the wave's
   wavy blue line, the samples' dots, the recovered wave's crimson */
::highlight(masthead-wave){color:var(--nav-ink);text-decoration-line:underline;
  text-decoration-style:wavy;text-decoration-color:var(--mh-sky);text-decoration-thickness:1px}
::highlight(masthead-dots){color:var(--nav-ink);text-decoration-line:underline;
  text-decoration-style:dotted;text-decoration-color:var(--nav-mute);text-decoration-thickness:2px}
::highlight(masthead-data){color:var(--mh-rose)}
@LIT@
/* His power of ten is MathML (build.py's PROF_HEADER), so a screen reader
   reads a power. It is set in the sentence's own face and size, the
   exponent at .66em, riding up on its own without opening the line. Chrome
   and Safari put MathML Core's default space after a script, a fifth of an
   em, after it (the face has no MATH table to say otherwise): with the word
   space that follows it read as a double space before "atoms", so the
   margin takes it back. Firefox adds only half a point there, and keeps it.
   A <sup> passed instead is set as the exponent is. */
.masthead__text math{font:inherit;letter-spacing:inherit;line-height:inherit}
.masthead__text msup{margin-inline-end:-.18em}
@supports (-moz-appearance:none){.masthead__text msup{margin-inline-end:0}}
.masthead__text msup>mn:last-child{font-size:.66em;letter-spacing:.01em}
.masthead__text sup{position:relative;top:-.62em;vertical-align:baseline;line-height:0;
  font-size:.66em;letter-spacing:.01em;margin-left:.04em}

/* The figure: as wide as the sentence, @HIGH0@px high in one row (@HIGH1@px in
   a phone's two), drawn by the script on a canvas; its formulas are MathML
   over it, on one baseline in a row of their own at the top of each row. It
   is there only where the page runs scripts (html.js is set before the
   first paint, so the band never changes height), and its height is the
   stylesheet's, so the script only follows it. */
.masthead__wave{position:relative;height:@HIGH0@px;max-width:@STRIP@px;margin:18px auto 0}
html:not(.js) .masthead__wave{display:none}
.masthead__cv{position:absolute;left:0;top:0;width:100%;height:100%;display:block}
/* Latin Modern Math, cut down as Site Math (site/mathtex.py), under a name of
   the band's own: the same file, so a page that has it has it once */
@font-face{font-family:"Masthead Math";src:url(fonts/site-math.woff2) format("woff2");
  font-display:block}
/* each formula is placed by the script, centred over its stage (translate)
   with its baseline on the row's; its arrival and its stepping back
   (opacity, transform, filter) are the script's too, a function of the
   story's clock. Hidden until placed. */
.masthead__tex{position:absolute;left:0;top:0;translate:-50% 0;white-space:nowrap;
  font-size:15px;line-height:1;color:var(--nav-mute);visibility:hidden;opacity:0;
  pointer-events:none}
.masthead__tex math{font-family:"Masthead Math","Site Math",math;font-size:1em}
.masthead__tex i{display:inline-block;width:0;height:0}
.masthead__tex .mh-sky{color:var(--mh-sky)}
.masthead__tex .mh-ink{color:var(--nav-ink)}
.masthead__tex .mh-rose{color:var(--mh-rose)}
.masthead__wave--set .masthead__tex{visibility:visible}
.masthead__wave--short .masthead__tex--long,
.masthead__wave:not(.masthead__wave--short) .masthead__tex--short{display:none}

/* the arrival: the sentence settles out of a blur */
@keyframes masthead-settle{from{opacity:0;transform:translateY(10px);filter:blur(6px)}}
@media (prefers-reduced-motion:no-preference){
  .masthead__text{animation:masthead-settle 800ms cubic-bezier(.23,1,.32,1) 60ms both}
}

/* a narrower band: the sentence steps down */
@container masthead (width < 820px){
  .masthead__in{padding:20px clamp(20px,3cqi,32px) 20px}
}
/* a phone: the sentence reads left-aligned, on the page's 22px edge, and the
   figure is told in two rows; on the narrowest the formulas step down to 14px
   so the second row's pair keeps its room */
@container masthead (width < @TWO@px){
  .masthead__in{padding:18px 22px 16px}
  .masthead__text{font-size:16px;line-height:1.58;text-align:left;text-wrap:pretty}
  .masthead__wave{height:@HIGH1@px;margin-top:16px}
}
@container masthead (width < @SMALL@px){
  .masthead__tex{font-size:14px}
}

/* Windows contrast themes: the band keeps its words; the figure is ornament */
@media (forced-colors:active){
  .masthead{border-bottom:1px solid CanvasText}
  .masthead__wave{display:none}
}
/* paper: dark words, no band, no figure */
@media print{
  .masthead{background:none;color:var(--ink)}
  .masthead__text{color:var(--ink)}
  .masthead__wave{display:none}
}
"""
for _k, _v in (("@HIGH0@", HIGH[0]), ("@HIGH1@", HIGH[1]), ("@STRIP@", STRIP),
               ("@TWO@", TWO), ("@SMALL@", SMALL), ("@LIT@", _lit())):
    CSS = CSS.replace(_k, str(_v))

# The script: his phrases first (found in his text, as ranges for
# CSS.highlights), then the figure. lay() measures the strip and places
# everything for its width; paint(t) draws the moment t of the story, a pure
# function of it; frame() advances the clock while the band is on screen and
# motion is welcome, and while the pointer's focus is still settling. build.py
# wraps every part's script in its own function scope.
JS = r"""
var band=document.querySelector('.masthead');
if(!band)return;
var said=band.querySelector('.masthead__text'),strip=band.querySelector('.masthead__wave'),
  cv=strip&&strip.querySelector('.masthead__cv'),D=@DATA@,S=D.st,E=D.sweep,END=D.end,TAU=2*Math.PI,
  RMQ=matchMedia('(prefers-reduced-motion: reduce)'),RM=RMQ.matches;
/* ---- his five phrases, as ranges: marked, and lit while their stage is told */
var PH=[],HL=!!(said&&window.Highlight&&window.CSS&&CSS.highlights),marked=[0,0,0,0,0],
  LIT=[],lit=[0,0,0,0,0],NL=D.levels;
(function(){
  if(!HL)return;
  var walk=document.createTreeWalker(said,NodeFilter.SHOW_TEXT),nodes=[],i,k,rx,hit,r,a,b;
  while(walk.nextNode())nodes.push(walk.currentNode);
  for(i=0;i<D.words.length;i++){
    rx=new RegExp(D.words[i].replace(/ /g,'\\s+'));
    for(k=0;k<nodes.length;k++){hit=rx.exec(nodes[k].data);if(!hit)continue;
      r=document.createRange();r.setStart(nodes[k],hit.index);r.setEnd(nodes[k],hit.index+hit[0].length);
      PH[i]=r;break}
  }
  for(i=1;i<=NL;i++){a=new Highlight();b=new Highlight();a.priority=b.priority=1;
    CSS.highlights.set('masthead-lit'+i,a);CSS.highlights.set('masthead-litd'+i,b);LIT.push([a,b])}
})();
function mark(i,on){
  if(!HL||!PH[i]||!D.marks[i]||marked[i]===on)return;marked[i]=on;
  if(on)CSS.highlights.set(D.marks[i],new Highlight(PH[i]));else CSS.highlights.delete(D.marks[i]);
}
function light(i,lv){
  if(!HL||!PH[i]||lit[i]===lv)return;var d=i===4?1:0;
  if(lit[i])LIT[lit[i]-1][d].delete(PH[i]);
  if(lv)LIT[lv-1][d].add(PH[i]);
  lit[i]=lv;
}
if(!strip||!cv||!cv.getContext){mark(2,1);mark(3,1);mark(4,1);return}
var ctx=cv.getContext('2d'),TG=[].slice.call(strip.querySelectorAll('.masthead__tex')).map(function(el){
    el.appendChild(document.createElement('i'));   /* a box on the baseline, to find it */
    return {el:el,k:+el.getAttribute('data-k'),o:-1,y:-1,b:-1}}),
  W=0,H=0,dpr=1,hair=1,L=null,C={},BX,BY,WX,WY,WU,RX,RY,RS,RC,KX,KY,grad=null,gradKey='',rose=null,roseKey='',
  T=0,raf=0,last=0,vis=true,PX=-1,PY=-1,hov=-1,hovT=-1,F=[1,1,1,1,1],G=[0,0,0,0,0],tap=0,X0=0,X1=0;
/* ---- time: manim's smooth, and Motion's spring with bounce 0 (motion.dev's
   spring(visualDuration) is critically damped, stiffness (2 pi / 1.2 v)^2) */
function cl(x){return x<0?0:x>1?1:x}
function sm(x){x=cl(x);return x*x*(3-2*x)}
function seg(t,t0,d){var x=cl((t-t0)/d);return x<.5?4*x*x*x:1-Math.pow(2-2*x,3)/2}
function settle(t,t0,v){var s=t-t0;if(s<=0)return 0;var a=TAU/(1.2*v);return 1-Math.exp(-a*s)*(1+a*s)}
function sinc(z){return Math.abs(z)<1e-9?1:Math.sin(Math.PI*z)/(Math.PI*z)}
function rgb(c,f){var m=/^#([0-9a-f]{6})$/i.exec(c),v=m?parseInt(m[1],16):f;return (v>>16)+','+(v>>8&255)+','+(v&255)}
function colours(){
  var s=getComputedStyle(band),g=function(n,f){return s.getPropertyValue(n).trim()||f};
  C.ink=g('--nav-ink','#fff');C.mute=g('--nav-mute','#c3cdd5');C.rule=g('--nav-rule','rgba(255,255,255,.14)');
  C.deep=g('--nav-deep','#001c35');C.sky=g('--mh-sky','#95c3ef');C.rose=g('--mh-rose','#ef7d86');
  C.skyRGB=rgb(C.sky,0x95c3ef);C.roseRGB=rgb(C.rose,0xef7d86);C.inkRGB=rgb(C.ink,0xffffff);gradKey=roseKey='';
}
/* a line w px wide centred on the device pixels, so a hairline is one pixel sharp */
function snap(v,w){var d=w*dpr;return (Math.round(v*dpr-d/2)+d/2)/dpr}
/* ---- the layout for the strip's width. The stylesheet decides one row or
   two (a phone): the script reads the strip's height and follows it. */
/* one row: the samples, and of them the recovered. Each formula of the
   right pair keeps D.pad on both sides over its stretch, the wave keeps at
   least D.minWave wavelengths, and between those bounds there are as many
   as make the space inside the right pair of formulas equal the space
   inside the left pair; null when the formulas cannot have that room */
function zones(tw){
  var g=L.g,gl=(L.ax-L.bx-L.bw/2)-(tw[0]+tw[1])/2,
    rmin=Math.max(D.minZ[1],Math.ceil((tw[3]+2*D.pad)/g)),dmin=Math.max(D.minZ[0],Math.ceil((tw[2]+2*D.pad)/g)),
    most=Math.floor((W-L.w0-D.minWave*L.lam)/g),nv=Math.round((2*gl+tw[2]+tw[3])/g),nr;
  if(rmin+dmin>most)return null;
  nv=Math.max(rmin+dmin,Math.min(most,nv));
  nr=Math.max(rmin,Math.round(nv*D.recShare));if(nv-nr<dmin)nr=nv-dmin;
  return [nv,nr];
}
function lay(){
  var w=strip.clientWidth,h=strip.clientHeight;if(!w||!h)return false;
  W=w;H=h;dpr=Math.min(2,window.devicePixelRatio||1);hair=1/dpr;
  cv.width=Math.round(W*dpr);cv.height=Math.round(H*dpr);
  var two=H>1.4*D.H[0],n=two?1:0,short=false,fk=parseFloat(getComputedStyle(TG[0].el).fontSize)/15||1,
    tw=function(k){return D.tw[k].map(function(v){return v*fk})},z,i,j,x,u,s,c,un,p;
  L={two:two,n:n,bx:D.bx};
  L.y=[D.axis[0],two?D.row2+D.axis[1]:D.axis[0]];    /* the physical row's axis, the data's */
  L.fb=[D.base,two?D.row2+D.base:D.base];             /* the formulas' baselines */
  L.bw=Math.max(D.bw[0],Math.min(D.bw[1],W*D.bw[2+n]));L.sc=L.bw/D.span;
  L.amp=Math.max(D.bAmp[0],Math.min(D.bAmp[1],L.sc*D.bAmp[2]));
  L.R=D.lens[n];L.ax=L.bx+L.bw+D.gapA[n]+L.R;L.w0=L.ax+L.R+2;
  L.lam=Math.max(D.lam[n][0],Math.min(D.lam[n][1],W*D.lam[n][2]));L.g=L.lam/D.perWave;L.A=D.amp[n];
  if(two){
    /* a phone: the wave runs to the first row's end; the second row is the
       data, samples from its start and the recovery on its right share */
    z=[Math.floor((W-L.bx)/L.g),Math.round(W*D.share2/L.g)];L.wu=2*W;
  }else{
    /* one row: the formulas whole where they have their room, else short */
    z=zones(tw(0));if(!z){short=true;z=zones(tw(1))||[D.minZ[0]+D.minZ[1],D.minZ[1]]}L.wu=W;
  }
  strip.classList.toggle('masthead__wave--two',two);
  strip.classList.toggle('masthead__wave--short',short);
  L.nv=z[0];L.nr=z[1];L.r0=W-L.nr*L.g;L.s0=W-L.nv*L.g;
  BX=new Float64Array(D.shape.length);BY=new Float64Array(D.shape.length);
  for(i=0;i<BX.length;i++)BX[i]=L.bx+i*D.node*L.sc;
  /* the wave, on the physical row from the atom to the row's end; u is its
     distance from the signal's end */
  x=Math.ceil((W-L.w0)/2)+1;WX=new Float64Array(x);WY=new Float64Array(x);WU=new Float64Array(x);
  for(i=0;i<WX.length;i++){WX[i]=Math.min(W-1.5,L.w0+2*i);WU[i]=L.wu-WX[i]}
  /* the recovery's two halves: sum_n sin(k u_n) sinc((u-u_n)/T) and the same
     with cos, over the samples on the page and D.virt more beyond the end;
     the wave's phase weighs them each frame */
  x=Math.ceil((W-L.r0)/2)+1;RX=new Float64Array(x);RY=new Float64Array(x);RS=new Float64Array(x);RC=new Float64Array(x);
  for(i=0;i<RX.length;i++){x=Math.min(W-1.5,L.r0+2*i);u=W-x;s=0;c=0;RX[i]=x;
    for(j=-D.virt;j<L.nv;j++){un=(j+.5)*L.g;z=sinc((u-un)/L.g);p=TAU*un/L.lam;s+=Math.sin(p)*z;c+=Math.cos(p)*z}
    RS[i]=s;RC[i]=c}
  KX=new Float64Array(Math.ceil(4*L.g)+2);KY=new Float64Array(KX.length);
  colours();place();
  return true;
}
/* the formulas: centred over their stages (the main span, the lens, the
   samples alone, the recovered wave), each with its baseline on its row's;
   pushed apart where two in a row would come closer than D.tagGap, and kept
   inside the strip */
function place(){
  var xs=[L.bx+L.bw/2,L.ax,(L.s0+L.r0)/2,(L.r0+W)/2],row=[0,0,1,1],on=[],i,j,k,a,b,o,g,w;
  for(i=0;i<TG.length;i++){g=TG[i];w=g.el.offsetWidth;g.on=!!w;if(!w)continue;
    g.row=row[g.k];g.x=xs[g.k];g.w=w;g.top=L.fb[g.row]-g.el.lastChild.offsetTop;on.push(g)}
  for(k=0;k<8;k++){
    for(j=0;j<on.length;j++){a=on[j];a.x=Math.max(2+a.w/2,Math.min(W-2-a.w/2,a.x))}
    for(j=0;j+1<on.length;j++){a=on[j];b=on[j+1];if(a.row!==b.row)continue;
      o=a.x+a.w/2+D.tagGap-(b.x-b.w/2);if(o>0){a.x-=o/2;b.x+=o/2}}
  }
  for(j=0;j<on.length;j++){a=on[j];a.el.style.left=a.x.toFixed(2)+'px';a.el.style.top=a.top.toFixed(2)+'px'}
  strip.classList.add('masthead__wave--set');
}
/* ---- each stage's weight: told, stepped back while the next is told, and
   at the end forward again one after another, in the order of his sentence;
   and the pointer's focus */
function em(i,t){
  var a=1;
  if(i<4&&t>S[i+1])a=1-(1-D.dim)*seg(t,S[i+1],.6);
  if(t>E)a+=(1-a)*seg(t,E+.1*i,.6);
  return a*F[i];
}
/* the pointer's focus eases in and out (a tenth of a second); true while it moves */
function focus(dt){
  var h=hov>=0?hov:hovT,k=dt>0?1-Math.exp(-dt/.09):0,more=false,i,f,g;
  for(i=0;i<5;i++){f=h<0||h===i?1:D.hovDim;g=h===i?1:0;
    F[i]+=(f-F[i])*k;G[i]+=(g-G[i])*k;
    if(Math.abs(F[i]-f)<.004)F[i]=f;else more=true;
    if(Math.abs(G[i]-g)<.004)G[i]=g;else more=true}
  return more;
}
/* once the story is told, the stage under the pointer lives: the deck
   swings on in its mode, the orbit's wave breathes on (X0, X1: the time they
   have run past the still figure, kept within one period). Let go, each
   runs on to the end of its period, which is its pose in the still figure,
   and stops there; true while one moves */
function live(dt){
  if(T<END||RM)return false;
  var h=hov>=0?hov:hovT,p=1/D.f1,q=D.atomP;
  if(h===0||X0>0){X0+=dt;if(X0>=p)X0=h===0?X0-p:0}
  if(h===1||X1>0){X1+=dt;if(X1>=q)X1=h===1?X1-q:0}
  return h===0||h===1||X0>0||X1>0;
}
/* ---- the drawing's small words */
function line(x0,y0,x1,y1){ctx.beginPath();ctx.moveTo(x0,y0);ctx.lineTo(x1,y1);ctx.stroke()}
function ring(x,y,r){ctx.beginPath();ctx.arc(x,y,r,0,TAU);ctx.stroke()}
function dot(x,y,r){ctx.beginPath();ctx.arc(x,y,r,0,TAU);ctx.fill()}
/* a polyline, x rising, between xa and xb */
function span(X,Y,n,xa,xb){
  if(n<2)return;if(xa<X[0])xa=X[0];if(xb>X[n-1])xb=X[n-1];if(xb-xa<.2)return;
  var i=0,f;while(i<n-2&&X[i+1]<=xa)i++;
  f=(xa-X[i])/((X[i+1]-X[i])||1);ctx.beginPath();ctx.moveTo(xa,Y[i]+(Y[i+1]-Y[i])*f);
  for(i++;i<n;i++){
    if(X[i]>=xb){f=(xb-X[i-1])/((X[i]-X[i-1])||1);ctx.lineTo(xb,Y[i-1]+(Y[i]-Y[i-1])*f);break}
    ctx.lineTo(X[i],Y[i])}
  ctx.stroke();
}
/* a polyline's height at x, or null off its ends */
function at(X,Y,x){
  var n=X.length,i;if(x<X[0]||x>X[n-1])return null;
  i=Math.max(0,Math.min(n-2,Math.floor((x-X[0])/((X[n-1]-X[0])/(n-1)||1))));
  while(i>0&&X[i]>x)i--;while(i<n-2&&X[i+1]<x)i++;
  return Y[i]+(Y[i+1]-Y[i])*(x-X[i])/((X[i+1]-X[i])||1);
}
/* the pen: a white point with a soft light of its line's colour, riding the
   head of a stroke while it is drawn; env() brings it in and takes it away */
function env(p){return sm(p/.08)*sm((1-p)/.2)}
function pen(x,y,a,c){
  a*=cl((W-7-x)/10);if(a<.02||y===null)return;   /* its light never reaches the edge */
  var g=ctx.createRadialGradient(x,y,0,x,y,7);
  g.addColorStop(0,'rgba('+c+','+(.55*a).toFixed(3)+')');g.addColorStop(1,'rgba('+c+',0)');
  ctx.globalAlpha=1;ctx.fillStyle=g;ctx.fillRect(x-7,y-7,14,14);
  ctx.globalAlpha=a;ctx.fillStyle=C.ink;dot(x,y,1.35);
}
/* the ground as TikZ hatches it, under a pin or a pier's footing */
function ground(x,y,w){
  var k;y=snap(y,1);ctx.beginPath();ctx.moveTo(x-w,y);ctx.lineTo(x+w,y);
  for(k=-w+2;k<=w;k+=3){ctx.moveTo(x+k,y);ctx.lineTo(x+k-2.5,y+2.5)}
  ctx.stroke();
}
/* a pinned support: its apex on the deck's underside, the ground under it */
function pin(x,y){
  ctx.lineJoin='miter';ctx.beginPath();ctx.moveTo(x,y+1.6);ctx.lineTo(x-3.5,y+6.8);ctx.lineTo(x+3.5,y+6.8);
  ctx.closePath();ctx.stroke();ctx.lineJoin='round';ground(x,y+6.8,5);
}
/* 1: the bridge. The pylons rise; the deck grows out from both at once,
   each stay taking its segment as the front passes, the side spans land on
   the abutments and the main span closes at its middle; then the finished
   deck swings in its first mode, at its own frequency, and comes to rest at
   the top of a swing, where its speed is zero */
function deckV(t){var s=Math.min(t,D.frz[0])-D.swing+X0;return s>0?L.amp*settle(s,0,.8)*Math.sin(TAU*D.f1*s):0}
function bridge(t,e){
  var t0=S[0],pp=seg(t,t0,.45);if(pp<=0||e<=0)return;
  var y0=L.y[0],sc=L.sc,bx=L.bx,n=BX.length,c0=t0+D.cant[0],pc=seg(t,c0,D.cant[1]),d=pc*D.half,
    side=Math.min(d,D.side),v=deckV(t),yt=y0-D.tower*sc,yf=y0+D.pier*sc,i,j,st,k,x,y,p,a,f;
  for(i=0;i<n;i++)BY[i]=y0+v*D.shape[i];
  /* the pylons, from their footings up, and the ground under them */
  ctx.lineCap='butt';ctx.strokeStyle=C.mute;ctx.lineWidth=D.lw[1];ctx.globalAlpha=.9*e;
  for(j=0;j<2;j++){x=snap(bx+D.pyl[j]*sc,D.lw[1]);line(x,yf,x,yf+(yt-yf)*pp)}
  ctx.lineWidth=1;ctx.globalAlpha=.6*e*sm(pp*2);
  for(j=0;j<2;j++)ground(bx+D.pyl[j]*sc,yf,6);
  /* the stays, each let down from its anchor as the deck's front passes it */
  ctx.lineWidth=hair;ctx.globalAlpha=.62*e;
  for(j=0;j<D.stays.length;j++){st=D.stays[j];p=seg(t,c0+D.cant[1]*st[3],.28);if(p<=0)continue;
    k=Math.round(st[0]/D.node);x=bx+st[1]*sc;y=y0-st[2]*sc;line(x,y,x+(BX[k]-x)*p,y+(BY[k]-y)*p)}
  /* the abutments' supports, as the side spans land on them */
  a=sm((d-D.side+6)/12);
  if(a>0){ctx.lineWidth=1;ctx.globalAlpha=.7*e*a;pin(bx,y0);pin(bx+L.bw,y0)}
  /* the deck */
  if(d<=0)return;
  ctx.lineCap='round';ctx.strokeStyle=C.sky;ctx.lineWidth=D.lw[0];ctx.globalAlpha=e;
  if(pc>=1)span(BX,BY,n,BX[0],BX[n-1]);
  else{span(BX,BY,n,bx+(D.pyl[0]-side)*sc,bx+(D.pyl[0]+d)*sc);span(BX,BY,n,bx+(D.pyl[1]-d)*sc,bx+(D.pyl[1]+side)*sc);
    /* a pen at each of the four fronts: the side ones go out as they land */
    f=env(pc)*e;a=f*sm((D.side-d)/14);
    pen(bx+(D.pyl[0]+d)*sc,y0,f,C.skyRGB);pen(bx+(D.pyl[1]-d)*sc,y0,f,C.skyRGB);
    pen(bx+(D.pyl[0]-side)*sc,y0,a,C.skyRGB);pen(bx+(D.pyl[1]+side)*sc,y0,a,C.skyRGB)}
}
/* 2: the point where the deck closed, taken out as a lens: the atom, its
   orbit and the matter wave standing on it, D.quantum wavelengths round */
function breath(t){return Math.cos(TAU*(Math.min(t,D.frz[1])-D.breath+X1)/D.atomP)}
function atom(t,e){
  var t0=S[1];if(t<t0||e<=0)return;
  var m=D.mid,sx=BX[m],sy=BY[m],r0=D.spyR,R=L.R,ax=L.ax,ay=L.y[0],q=settle(t,t0,.3),f=settle(t,t0+.15,.55),
    pn=settle(t,t0+.55,.25),po=seg(t,t0+.6,.5),pw=seg(t,D.breath,.6),ro=R*D.orbit,a,k,th,rr,x,y,cx,cy,cr;
  ctx.lineWidth=1;ctx.strokeStyle=C.mute;
  ctx.globalAlpha=.85*e*cl(q*1.5);ring(sx,sy,r0*(.55+.45*q));
  if(t>t0+.15){cx=sx+(ax-sx)*f;cy=sy+(ay-sy)*f;cr=r0+(R-r0)*f;
    /* the lens covers what it passes over */
    ctx.globalAlpha=e;ctx.fillStyle=C.deep;dot(cx,cy,cr);
    ctx.globalAlpha=.85*e*cl((t-t0-.15)/.12);ring(cx,cy,cr)}
  if(pn>0){ctx.globalAlpha=e*cl(pn*1.5);ctx.fillStyle=C.ink;dot(ax,ay,D.nucleus*(.5+.5*pn))}
  if(po>0){th=-Math.PI/2-TAU*po;ctx.globalAlpha=.5*e;ctx.setLineDash([1.2,2.4]);ctx.beginPath();
    ctx.arc(ax,ay,ro,-Math.PI/2,th,true);ctx.stroke();ctx.setLineDash([]);
    pen(ax+ro*Math.cos(th),ay+ro*Math.sin(th),env(po)*e,C.skyRGB)}
  if(pw>0){a=R*D.ripple*pw*breath(t);
    ctx.globalAlpha=e*cl(pw*3);ctx.strokeStyle=C.sky;ctx.lineWidth=D.lw[0];ctx.beginPath();
    for(k=0;k<=180;k++){th=TAU*k/180;rr=ro+a*Math.cos(D.quantum*th);
      x=ax+rr*Math.cos(th);y=ay-rr*Math.sin(th);if(k)ctx.lineTo(x,y);else ctx.moveTo(x,y)}
    ctx.closePath();ctx.stroke()}
}
/* the wave's phase, in wavelengths: it drifts one wavelength each D.P
   seconds, and from the sweep eases to rest in D.dec (its speed falling as
   (1 - x)^2, so it never jerks) */
function tau(t){
  var s=Math.max(0,t-S[2]),se=E-S[2],x;
  if(s<=se)return D.ph0+s/D.P;
  x=cl((s-se)/D.dec);return D.ph0+(se+D.dec*(1-Math.pow(1-x,3))/3)/D.P;
}
/* 3: the wave leaves the atom and runs on; over the samples it fades (4).
   On a phone it runs off the first row's end, and thins out there */
function wave(t,e){
  var t0=S[2];if(t<t0||e<=0)return;
  var p=seg(t,t0,D.wdur[L.n]),ph=tau(t),y0=L.y[0],A=L.A,n=WX.length,fd=L.two?0:seg(t,S[3]+.8,.6),i,x,s,xh,key;
  for(i=0;i<n;i++){x=WX[i];s=sm((x-L.w0)/(.35*L.lam));WY[i]=y0-A*s*Math.sin(TAU*(WU[i]/L.lam+ph))}
  key=e.toFixed(3)+'/'+fd.toFixed(3);
  if(key!==gradKey){gradKey=key;
    if(L.two){grad=ctx.createLinearGradient(W-.3*L.lam,0,W,0);x=.2}
    else{grad=ctx.createLinearGradient(L.s0-40,0,L.s0+40,0);x=1-fd}
    grad.addColorStop(0,'rgba('+C.skyRGB+','+e.toFixed(3)+')');
    grad.addColorStop(1,'rgba('+C.skyRGB+','+(e*x).toFixed(3)+')')}
  ctx.globalAlpha=1;ctx.strokeStyle=grad;ctx.lineWidth=D.lw[0];ctx.lineCap='round';
  xh=L.w0+(W-L.w0)*p;span(WX,WY,n,WX[0],xh);
  if(p<1)pen(xh,at(WX,WY,xh),env(p)*e,C.skyRGB);
}
/* 4 and 5: the samples, x[n] = x(nT), and what is recovered from them */
function data(t,e3,e4){
  var t0=S[3];if(t<t0)return;
  var y0=L.y[1],A=L.A,g=L.g,ph=tau(t),c=Math.cos(TAU*ph),s=Math.sin(TAU*ph),t4=S[4],
    i,n,x,j,q,val,y,ee,ka,a0,a1,m,xx,st,pr;
  /* the axis they stand on */
  ctx.globalAlpha=Math.max(e3,e4);ctx.strokeStyle=C.rule;ctx.lineWidth=hair;ctx.lineCap='butt';
  y=snap(y0,hair);line(L.s0,y,L.s0+(W-1.5-L.s0)*seg(t,t0,.6),y);
  if(t>=t4){
    /* each sample's sinc rises, then fades as their sum is drawn */
    st=Math.min(.045,.8/L.nr);ka=.42*(1-seg(t,t4+1.5,.5));
    if(ka>0){ctx.strokeStyle=C.rose;ctx.lineWidth=hair;ctx.lineCap='round';
      for(n=0;n<L.nv;n++){x=W-(n+.5)*g;if(x<L.r0)continue;j=Math.round((x-L.r0-g/2)/g);
        q=settle(t,t4+st*j,.35);if(q<=0)continue;
        val=A*Math.sin(TAU*((n+.5)*g/L.lam+ph))*q;a0=Math.max(L.r0-2*g,x-4*g);a1=Math.min(W-1.5,x+4*g);m=0;
        for(xx=a0;xx<=a1+.01&&m<KX.length;xx+=2){KX[m]=xx;KY[m]=y0-val*sinc((xx-x)/g);m++}
        ctx.globalAlpha=ka*e4*cl(q*2);span(KX,KY,m,KX[0],KX[m-1])}}
    for(i=0;i<RX.length;i++)RY[i]=y0-A*(RS[i]*c+RC[i]*s);
    if(roseKey!==e4.toFixed(3)){roseKey=e4.toFixed(3);rose=ctx.createLinearGradient(L.r0,0,L.r0+2*g,0);
      rose.addColorStop(0,'rgba('+C.roseRGB+',0)');rose.addColorStop(1,'rgba('+C.roseRGB+','+roseKey+')')}
    pr=seg(t,t4+.4,D.rdur);x=L.r0+(W-L.r0)*pr;
    ctx.globalAlpha=1;ctx.strokeStyle=rose;ctx.lineWidth=D.lw[2];ctx.lineCap='round';span(RX,RY,RX.length,RX[0],x);
    if(pr>0&&pr<1)pen(x,at(RX,RY,x),env(pr)*e4*cl((x-L.r0)/(2*g)),C.roseRGB);
  }
  /* the samples: a stem and a point every T, dropped in turn from the left */
  ctx.lineWidth=1;ctx.lineCap='butt';st=Math.min(.032,.9/L.nv);
  for(n=L.nv-1;n>=0;n--){
    x=W-(n+.5)*g;j=L.nv-1-n;q=settle(t,t0+.2+st*j,.28);if(q<=0)continue;
    val=A*Math.sin(TAU*((n+.5)*g/L.lam+ph));y=y0-val*q;ee=x<L.r0?e3:Math.max(e3,e4);xx=snap(x,1);
    ctx.globalAlpha=.5*ee;ctx.strokeStyle=C.mute;line(xx,y0,xx,y);
    ctx.globalAlpha=ee*cl(q*1.6);ctx.fillStyle=C.ink;dot(xx,y,D.dot);
  }
}
/* ---- the probe: where the pointer is, the stage under it, read there */
function region(x,y){
  if(L.two&&y>D.row2-4)return x<L.r0?3:4;
  return x<L.bx+L.bw+D.gapA[L.n]/2?0:x<L.w0+4?1:L.two||x<L.s0?2:x<L.r0?3:4;
}
function probe(t){
  if(PX<0||hov<0)return;
  var h=hov,x=PX,y=null,y0=L.y[h>2?1:0],n,r,th,stem=h>1;
  if(h===0&&t>D.swing)y=at(BX,BY,x);
  else if(h===1&&t>D.breath+.3){th=Math.atan2(y0-PY,x-L.ax);
    r=L.R*D.orbit+L.R*D.ripple*seg(t,D.breath,.6)*breath(t)*Math.cos(D.quantum*th);
    ctx.globalAlpha=.55;ctx.strokeStyle=C.ink;ctx.lineWidth=hair;
    x=L.ax+r*Math.cos(th);y=y0-r*Math.sin(th);line(L.ax,y0,x,y);stem=false}
  else if(h===2&&t>S[2]+D.wdur[L.n])y=at(WX,WY,x);
  else if(h===3&&t>S[3]+1.2){n=Math.max(0,Math.min(L.nv-1,Math.round((W-x)/L.g-.5)));x=snap(W-(n+.5)*L.g,1);
    y=y0-L.A*Math.sin(TAU*((n+.5)*L.g/L.lam+tau(t)))}
  else if(h===4&&t>S[4]+.4+D.rdur)y=at(RX,RY,x);
  if(y===null)return;
  ctx.strokeStyle=C.ink;ctx.fillStyle=C.ink;ctx.lineWidth=1;ctx.lineCap='butt';
  if(stem){ctx.globalAlpha=.7;x=snap(x,1);line(x,y0,x,y)}
  ctx.globalAlpha=.6;ring(x,y,4.5);ctx.globalAlpha=1;dot(x,y,2)
}
/* ---- his words and the formulas, in step with the figure */
function words(t){
  var i,a,b;
  for(i=2;i<5;i++)mark(i,t>=S[i]?1:0);
  for(i=0;i<5;i++){a=cl((t-S[i])/.35);b=cl(((i<4?S[i+1]:E)+.35-t)/.35);
    light(i,Math.round(NL*Math.max(Math.min(a,b),G[i])))}
}
function formulas(t){
  var i,g,k,q,o,y,b;
  for(i=0;i<TG.length;i++){g=TG[i];if(!g.on)continue;k=g.k;
    q=settle(t,D.tagAt[k],.4);o=seg(t,D.tagAt[k],.45)*(.4+.6*em(D.tagStage[k],t));
    o=Math.round(o*1e3)/1e3;y=Math.round(6*(1-q)*100)/100;b=Math.round(3*(1-cl(q*1.25))*10)/10;
    if(o!==g.o){g.o=o;g.el.style.opacity=o}
    if(y!==g.y){g.y=y;g.el.style.transform=y?'translateY('+y+'px)':''}
    if(b!==g.b){g.b=b;g.el.style.filter=b?'blur('+b+'px)':''}}
}
function paint(t){
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,W,H);ctx.lineJoin='round';
  var e3=em(3,t),e4=em(4,t);
  bridge(t,em(0,t));atom(t,em(1,t));wave(t,em(2,t));data(t,e3,e4);probe(t);
  ctx.globalAlpha=1;words(t);formulas(t);
}
/* ---- the clock: it runs while the story is told (on screen, in a visible
   tab, for a reader who has not asked for less motion) and while the
   pointer's focus settles; then it stops */
function busy(){return !RM&&T<END}
function frame(ts){
  raf=0;if(!vis)return;
  var dt=last?Math.min(.05,(ts-last)/1000):0,more;last=ts;
  if(busy())T=Math.min(END,T+dt);
  more=focus(dt);more=live(dt)||more;paint(T);
  if(busy()||more)raf=requestAnimationFrame(frame);else last=0;
}
function kick(){if(!raf&&L&&vis){last=0;raf=requestAnimationFrame(frame)}}
function halt(){if(raf)cancelAnimationFrame(raf);raf=0;last=0}
var look=0;
function sync(){look=0;var r=band.getBoundingClientRect();
  vis=!document.hidden&&r.bottom>0&&r.top<innerHeight;if(!vis)halt();else if(busy())kick()}
function soon(){if(!look)look=requestAnimationFrame(sync)}
addEventListener('scroll',soon,{passive:true});
addEventListener('resize',soon);
document.addEventListener('visibilitychange',sync);
function resized(){var w=strip.clientWidth,h=strip.clientHeight;if(!w||w===W&&h===H&&L)return;if(!lay())return;
  paint(T);sync()}
if(window.ResizeObserver)new ResizeObserver(resized).observe(strip);else addEventListener('resize',resized);
if(document.fonts&&document.fonts.load)document.fonts.load('15px "Masthead Math"').then(function(){if(L){place();paint(T)}},function(){});
if(RMQ.addEventListener)RMQ.addEventListener('change',function(){RM=RMQ.matches;if(RM){halt();T=END;paint(T)}else sync()});
/* ---- the pointer: a probe over the figure, a finger on his words */
function point(e){var r=strip.getBoundingClientRect();PX=e.clientX-r.left;PY=e.clientY-r.top;hov=region(PX,PY);kick()}
strip.addEventListener('pointermove',function(e){if(e.pointerType!=='touch'&&L)point(e)},{passive:true});
strip.addEventListener('pointerleave',function(e){if(e.pointerType!=='touch'){PX=-1;hov=-1;kick()}});
strip.addEventListener('pointerdown',function(e){
  if(e.pointerType==='mouse'||!L)return;point(e);
  clearTimeout(tap);tap=setTimeout(function(){PX=-1;hov=-1;kick()},2200);
},{passive:true});
function phrase(x,y){
  var n=null,o=0,p,i,r;
  if(document.caretPositionFromPoint){p=document.caretPositionFromPoint(x,y);if(p){n=p.offsetNode;o=p.offset}}
  else if(document.caretRangeFromPoint){p=document.caretRangeFromPoint(x,y);if(p){n=p.startContainer;o=p.startOffset}}
  if(!n)return -1;
  for(i=0;i<5;i++){r=PH[i];if(r&&r.isPointInRange(n,o)&&!(n===r.endContainer&&o===r.endOffset))return i}
  return -1;
}
if(HL){
  said.addEventListener('pointermove',function(e){
    if(e.pointerType==='touch')return;var h=phrase(e.clientX,e.clientY);if(h!==hovT){hovT=h;kick()}
  },{passive:true});
  said.addEventListener('pointerleave',function(e){if(e.pointerType!=='touch'&&hovT>=0){hovT=-1;kick()}});
  said.addEventListener('pointerdown',function(e){
    if(e.pointerType==='mouse')return;var h=phrase(e.clientX,e.clientY);if(h<0)return;hovT=h;kick();
    clearTimeout(tap);tap=setTimeout(function(){hovT=-1;kick()},2200);
  },{passive:true});
}
/* any moment of the story, drawn and held (to look at one frame) */
band.__mh={at:function(t){halt();T=t;PX=-1;hov=hovT=-1;F=[1,1,1,1,1];G=[0,0,0,0,0];X0=X1=0;paint(t)},
  layout:function(){return L},time:function(){return T},play:function(){sync()}};
/* back on the page by the browser's history, the story has been told: the
   figure is shown whole and still, as it is to a reader who asked for less
   motion */
try{var nav=performance.getEntriesByType('navigation')[0];if(nav&&nav.type==='back_forward')T=END}catch(e){}
if(RM)T=END;
if(lay()){paint(T);sync()}
"""
JS = JS.replace("@DATA@", json.dumps(DATA, separators=(",", ":")))

# Fallback only: build.py passes PROF_HEADER, which this copies character for
# character. It is inline HTML with no block around it.
_HEADER = """From elastic waves causing dynamic vibrations in a bridge to the matter waves
inside a single atom (fun fact: roughly <math><mn>7</mn> <mo>&times;</mo> <msup><mn>10</mn><mn>27</mn></msup></math> atoms in a
human body), wave motion sits at the center of the physical world. What we observe, though,
arrives as discrete measurements. Data analytics is how we recover the information behind
those numbers, and how we make it useful."""


def render(text_html=None):
    """Return the masthead band as an HTML string.

    text_html: his sentence as inline HTML (build.py's PROF_HEADER), inserted
    exactly as given. Should it arrive already wrapped in a <p>, it is not
    wrapped again.
    """
    text = _HEADER if text_html is None else text_html
    if text.lstrip().startswith("<p"):
        body = f'<div class="masthead__text">{text}</div>'
    else:
        body = f'<p class="masthead__text">{text}</p>'
    return f'<div class="masthead"><div class="masthead__in">{body}{_WAVE}</div></div>'
