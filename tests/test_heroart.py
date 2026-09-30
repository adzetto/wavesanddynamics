"""The home page illustration's vibration: the tall building and the bridge.

On 25 Sep 2026 the professor asked for the tall building and the bridge to
vibrate "at least like before" (round 4's draft b rocked the building and rang
the deck once a loop; the merge had dropped both). These hold what was built
for it in site/parts/heroart.py, "the vibration": SMIL, so that WebKit bends
the bridge as well; one loop of the story that leaves rest and comes back to
it; swings large enough to see and small enough to believe; the building's
answer to the acoustic source at its foot and the span's to the trains; the
reflection and the roof's sensor moving with their structure; a script that
begins, pauses and rests it with the story; and the figure's markup budget.

On 26 Sep 2026 his iPhone showed no car, no train and no trace, the three
parts that moved inside a window with overflow hidden, and he asked whether
the airplane's wing could move too; the developer added that the story must
always play. So these also hold the travellers (the train, the car and the
trace moving by SMIL in the drawing, never absent for long), the wings'
first bending mode, and a figure with no pause button and nothing that
holds the story.
"""

import math
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

from parts import heroart as ha  # noqa: E402

MARKUP = ha.render()


def smil(markup=MARKUP):
    """Every SMIL animation in markup, as its attributes, in document order."""
    return [dict(re.findall(r'([\w-]+)="([^"]*)"', attrs))
            for attrs in re.findall(r"<animate(?:Transform)?\b([^>]*)/>", markup)]


def times(a):
    return [float(t) * ha.T for t in a["keyTimes"].split(";")]


def numbers(value):
    return [float(v) for v in re.findall(r"-?\d*\.?\d+", value)]


def group(markup, gid):
    """The markup of <g id=gid>, its own </g> included."""
    start = markup.index(f'<g id="{gid}">')
    depth, i = 0, start
    for m in re.finditer(r"<g\b|</g>", markup[start:]):
        depth += 1 if m.group() != "</g>" else -1
        if depth == 0:
            i = start + m.end()
            break
    return markup[start:i]


LEANS = [a for a in smil() if a.get("type") == "skewX"]
BENDS = [a for a in smil() if a.get("attributeName") == "d"]


# ------------------------------------------------------------- how it moves

def test_the_building_and_the_bridge_move_by_smil_not_by_css_d():
    # WebKit animates no CSS d, so a bridge bent by it stood still in Safari
    assert "d:path(" not in ha.CSS and "#ha-b2" not in ha.CSS
    assert "skewX" not in ha.CSS
    assert len(LEANS) == 4 and len(BENDS) == 3
    assert all(a["additive"] == "sum" for a in LEANS + BENDS)
    assert group(MARKUP, "ha-b2").count("<animateTransform") == 2
    assert group(MARKUP, "ha-dk").count("<animate ") == 2


def test_one_animation_begins_with_the_story_and_the_rest_follow_it():
    begins = [a["begin"] for a in smil()]
    assert begins.count("indefinite") == 1
    master = next(a for a in smil() if a["begin"] == "indefinite")
    # a hyphen in an id reads as an offset in a SMIL time reference
    assert master["id"] == "ha_vib" and "-" not in master["id"]
    assert all(b == "ha_vib.begin" for b in begins if b != "indefinite")
    # outside anything a <use> repeats, so it is begun once
    defs = MARKUP[MARKUP.index("<defs>"):MARKUP.index("</defs>")]
    assert 'id="ha_vib"' in defs
    assert 'id="ha_vib"' not in group(MARKUP, "ha-b2") + group(MARKUP, "ha-dk")


def test_every_animation_is_one_loop_of_the_story_from_rest_to_rest():
    for a in smil():
        assert a["dur"] == f"{ha.T:g}s" and a["repeatDur"] == "indefinite"
        assert a["calcMode"] == "spline"
        ts, values = times(a), a["values"].split(";")
        assert ts[0] == 0 and ts[-1] == ha.T
        assert all(p < q for p, q in zip(ts, ts[1:]))
        assert len(values) == len(ts) == len(a["keySplines"].split(";")) + 1
    # the picture at rest is the loop's first and last frame: a vibration
    # leaves rest and comes back to it (a traveller ends a whole turn on,
    # test_the_travellers_end_their_loop_where_it_began)
    for a in LEANS + BENDS:
        values = a["values"].split(";")
        for v in (values[0], values[-1]):
            assert not any(numbers(v)), v


def test_the_splines_are_sine_like():
    def ease(x1, y1, x2, y2):
        def f(u):
            lo, hi = 0.0, 1.0
            for _ in range(50):
                m = (lo + hi) / 2
                x = 3 * x1 * m * (1 - m) ** 2 + 3 * x2 * m * m * (1 - m) + m ** 3
                lo, hi = (m, hi) if x < u else (lo, m)
            m = (lo + hi) / 2
            return 3 * y1 * m * (1 - m) ** 2 + 3 * y2 * m * m * (1 - m) + m ** 3
        return f
    shapes = ((ha.SINE_INOUT, lambda u: (1 - math.cos(math.pi * u)) / 2),
              (ha.SINE_OUT, lambda u: math.sin(math.pi * u / 2)),
              (ha.SINE_IN, lambda u: 1 - math.cos(math.pi * u / 2)))
    for spline, sine in shapes:
        f = ease(*numbers(spline))
        assert max(abs(f(i / 100) - sine(i / 100)) for i in range(101)) < 0.015, spline


# --------------------------------------------------------- what it looks like

def swings(period, env):
    return ha._swings(period, env)[1:-1]


def test_the_swings_alternate_and_stay_small_enough_to_believe():
    # never still, never more than about 3% of the building's height or 4% of
    # the span, and each swing the other way from the last
    for period, env in ((ha.SWAY_P, ha._sway_env), (ha.SPAN_P, ha._span_env)):
        vs = [v for _, v, _ in swings(period, env)]
        assert all(p * q < 0 for p, q in zip(vs, vs[1:]))
        assert all(2 <= abs(v) <= 8.5 for v in vs)
    # large enough to see at the desktop size (0.39 px a unit): 3 px at the peaks
    assert max(abs(v) for _, v, _ in swings(ha.SWAY_P, ha._sway_env)) >= 7.5
    assert max(abs(v) for _, v, _ in swings(ha.SPAN_P, ha._span_env)) >= 7.5


def test_the_building_rings_when_the_acoustic_source_does_and_dies_away():
    sw = [(t, abs(v)) for t, v, _ in swings(ha.SWAY_P, ha._sway_env)]
    peak = max(sw, key=lambda s: s[1])
    # the first swing after the source rings (0.42 s) is the largest
    assert peak[0] == min(t for t, _ in sw if t > 0.42)
    assert all(v < 3 for t, v in sw if t < 0.42)
    after = [v for t, v in sw if peak[0] <= t <= peak[0] + 4]
    assert all(p > q for p, q in zip(after, after[1:]))


def test_the_span_swells_under_the_trains_and_rings_down():
    sw = [(t, abs(v)) for t, v, _ in swings(ha.SPAN_P, ha._span_env)]
    peak = max(sw, key=lambda s: s[1])
    # the trains run from 2.75 s and stop at 5.15 s; the tower sensor fires at 5.4 s
    assert 4.9 <= peak[0] <= 5.5
    assert all(v < 3 for t, v in sw if t < 2.75)
    before = [v for t, v in sw if 2.75 <= t <= peak[0]]
    after = [v for t, v in sw if peak[0] <= t <= peak[0] + 3]
    assert all(p < q for p, q in zip(before, before[1:]))
    assert all(p > q for p, q in zip(after, after[1:]))


def test_the_building_sways_in_its_first_mode():
    # every floor swings in step, as in any mode of a building fixed at its
    # foot: the upper half's own lean has the whole's times and splines
    # (until 27 Sep 2026 the roof led the middle by 0.2 s)
    whole, top = LEANS[:2]
    assert times(whole) == times(top) and whole["keySplines"] == top["keySplines"]
    # and is UPPER of the whole's, swing for swing (to the two decimals of a
    # degree the lists carry), so the middle moves 0.4 of the roof
    for a, b in zip(numbers(whole["values"])[1:-1], numbers(top["values"])[1:-1]):
        want = ha.UPPER * math.tan(math.radians(a))
        assert math.tan(math.radians(b)) == pytest.approx(want, rel=0.02, abs=5e-4)
    assert (ha.G - ha.MID) / ha.ROOF == pytest.approx(0.4, abs=0.001)


def test_the_leans_bring_the_roof_to_the_envelope():
    whole, top = LEANS[:2]
    roof = [(ha.G - 308) * math.tan(math.radians(-a)) for a in numbers(whole["values"])]
    want = [v for _, v, _ in ha._swings(ha.SWAY_P, ha._sway_env)]
    # the whole's lean alone carries the roof 247 / ROOF of the way
    for r, w in zip(roof, want):
        assert abs(r - w * (ha.G - 308) / ha.ROOF) < 0.06


def test_the_roofs_sensor_leans_with_the_building():
    ring = MARKUP.index('<circle class="hrg" cx="218" cy="308"')
    before = MARKUP[:ring]
    # the ring sits in the same two leans as the building, drawn over the links
    lean_tags = re.findall(r"<animateTransform\b[^>]*/>", before)[-2:]
    building = re.findall(r"<animateTransform\b[^>]*/>", group(MARKUP, "ha-b2"))
    assert lean_tags == building
    assert before.rindex("<animateTransform") > before.rindex('class="hl')


def test_the_reflection_repeats_the_moving_structures():
    refl = MARKUP[MARKUP.index('<g class="hrefl"'):]
    assert '<use href="#ha-b2"/>' in refl and '<use href="#ha-dk"/>' in refl


def test_the_main_spans_hangers_follow_the_bend():
    dk = group(MARKUP, "ha-dk")
    clipped = re.findall(r'<path [^>]*clip-path="url\(#ha-cgap\)"[^>]*d="([^"]*)"', MARKUP)
    # the main span's hangers and the three groups of the wave over them
    assert len(clipped) == 4
    xs = sorted({round(float(x), 1) for d in clipped for x in re.findall(r"M(\d+\.?\d*)", d)})
    assert xs == [round(x, 1) for x in ha.HANGERS if 496 < x < 696]
    # the side spans' hangers hold, unclipped
    side = [x for x in ha.HANGERS if not 496 < x < 696]
    assert all(f"M{ha._n(x)} " in dk for x in side)
    # the room between cable and deck bends as they do: every value drops the
    # same control points by the same amount
    gap, cable, span = (next(a for a in BENDS if a.get("id") == "ha_vib"),
                        *[a for a in BENDS if a.get("id") != "ha_vib"])
    assert cable["values"] == span["values"]
    for g, c in zip(gap["values"].split(";"), cable["values"].split(";")):
        drop = numbers(c)[3]                  # M0 0q0 <drop> 0 0
        assert numbers(g)[3] == drop and numbers(g)[8] == drop   # ...V0q0 <drop> 0 0Z


def test_the_bridge_at_rest_is_the_reference():
    # the main cable is the reference's parabola, the deck its band 478 to 486.5
    x, y = 496, 343
    dx1, dy1, dx2, dy2 = numbers(ha.CABLE)[2:]
    assert (x + dx1, y + dy1, x + dx2, y + dy2) == (596, 448, 696, 343)
    assert numbers(ha.SPAN)[:2] == [496, 482.25] and 'stroke-width="8.5"' in group(MARKUP, "ha-dk")
    for x0 in (402, 694):
        assert f'<rect class="hf-i" x="{x0}" y="478" width="96" height="8.5" rx="1.5"/>' in MARKUP


# ------------------------------------------------------------------ the script

def test_the_script_begins_pauses_and_rests_it_with_the_story():
    js = ha.JS
    assert "getElementById('ha_vib')" in js
    assert js.count("beginElement()") == 1        # once, with the story
    assert "svg.unpauseAnimations()" in js and "svg.pauseAnimations()" in js
    # held at rest when motion is not wanted and while printing
    rm = js[js.index("if(RM.matches){"):js.index("var run=")]
    assert "rest()" in rm
    assert "beforeprint" in js and "afterprint" in js
    assert "endElement" not in js     # an ended animation does not restart alike everywhere


def test_the_figure_stays_within_its_markup_budget():
    # design/ROUND4_SPEC.md section 4: markup under 60 KB (heroart.md counts 1000 bytes a KB)
    assert len(MARKUP.encode()) < 60_000


def test_no_dash_in_the_part():
    src = open(ha.__file__, encoding="utf-8").read()
    assert "—" not in src and " – " not in src


# ------------------------------------------------------------- the travellers

TRANSLATES = [a for a in smil() if a.get("type") == "translate"]


def drawing():
    """The drawing's own <svg>, to its last tag."""
    start = MARKUP.index('<svg class="ha__svg"')
    depth = 0
    for m in re.finditer(r"<svg\b|</svg>", MARKUP[start:]):
        depth += 1 if m.group() != "</svg>" else -1
        if depth == 0:
            return MARKUP[start:start + m.end()]


def test_no_part_moves_inside_a_window():
    # Safari on the professor's iPhone drew none of the parts that moved in
    # a box with overflow hidden: no such box is left
    assert "ha__w" not in MARKUP and "ha__w" not in ha.CSS
    # (the one box left with overflow hidden is the keys' screen-reader text)
    rules = re.findall(r"([^{}]+)\{[^}]*overflow:hidden", ha.CSS)
    assert [r.strip() for r in rules] == [".ha__sr"]
    for gone in ("mtrn", "mcar", "mtape", "ha-mr", "ha-csil"):
        assert gone not in MARKUP and gone not in ha.CSS, gone


def test_the_travellers_move_by_smil_in_the_drawing():
    svg = drawing()
    for gid in ("ha-trn", "ha-car"):
        g = group(svg, gid)
        assert g.count('type="translate"') == 1, gid
        # the reflection repeats it, moving with it
        assert f'<use href="#{gid}"/>' in svg[svg.index('<g class="hrefl"'):]
    assert 'clip-path="url(#ha-ctrn)"' in group(svg, "ha-trn")
    tape = svg[svg.index('id="ha-tp"') - 400:]
    assert 'clip-path="url(#ha-ctape)"' in tape and 'type="translate"' in tape
    # the train's ring and the car's travel with them: 2 vehicles, 2 rings, the trace
    assert len(TRANSLATES) == 5
    assert all(a["begin"] == "ha_vib.begin" for a in TRANSLATES)


def test_the_travellers_end_their_loop_where_it_began():
    train, car = TRANSLATES[0], TRANSLATES[1]
    assert numbers(train["values"])[0] == 0 and numbers(train["values"])[-1] == ha.SHIFT
    # two trains, a whole train apart: the one that arrives stands where the
    # one that left stood
    assert f'<use href="#ha-tr0" x="-{ha.SHIFT}"/>' in MARKUP
    assert numbers(car["values"])[0] == 0 == numbers(car["values"])[-1]
    tape = TRANSLATES[-1]
    assert numbers(tape["values"]) == [-ha.TAPE, 0]
    assert f'<use href="#ha-tp" x="{ha.TAPE}"/>' in MARKUP


def test_the_train_is_always_in_sight():
    # wherever the pair stands, at least three quarters of a train shows
    # between the two buildings
    x0, _, w, _ = ha.TRAIN_CLIP
    body = (356, 812)
    shortest = min(sum(max(0, min(body[1] + s + dx, x0 + w) - max(body[0] + s + dx, x0))
                       for dx in (0, -ha.SHIFT)) for s in range(0, ha.SHIFT + 1, 5))
    assert shortest >= 0.75 * (body[1] - body[0])


def test_the_car_is_never_away_for_long():
    moves = ha._car_moves()
    away = [(t, u) for (t, x, _), (u, y, _) in zip(moves, moves[1:]) if x == y == ha.CAR_GO]
    assert len(away) == 1 and away[0][1] - away[0][0] <= 0.25
    gone, back = next(t for t, x, _ in moves if x == ha.CAR_GO), moves[-2][0]
    # parked for at least nine seconds of the twelve, out and back in under three
    assert back - moves[1][0] < 3 and ha.T - (back - moves[1][0]) >= 9
    assert ha.CAR_GO + 962 >= ha.VB[0] + ha.VB[2]      # it really leaves the picture
    assert gone < back


def test_the_trace_is_always_drawn():
    # its three turns cover its clip at every point of its scroll
    x0, _, w, _ = ha.TAPE_CLIP
    assert x0 == ha.VB[0] and x0 + w == ha.RIP[0]
    lo, hi = min(numbers(TRANSLATES[-1]["values"])), max(numbers(TRANSLATES[-1]["values"]))
    assert 0 + hi <= x0 and 3 * ha.TAPE + lo >= x0 + w
    # drawn in the drawing, after the axis it runs along
    svg = drawing()
    assert svg.index('id="ha-tp"') > svg.index(f'd="M58 {ha.RIP[1]}H1248"')


# ------------------------------------------------------------------ the wings

def wing_keyframes(name):
    """A panel's @keyframes as (skewY degrees, scaleY) per stop, in order."""
    body = re.search(r"@keyframes %s\{(.*?)\}\}" % name, ha.CSS).group(1)
    return [(float(a), float(b)) for a, b in
            re.findall(r"skewY\((-?\.?\d*\.?\d+)deg\) scaleY\((-?\.?\d*\.?\d+)\)", body)]


def shear(p, pivot, skew, scale):
    """p after skewY(skew) scaleY(scale) about pivot (CSS: x kept, y' = tan x + s y)."""
    x, y = p[0] - pivot[0], p[1] - pivot[1]
    return pivot[0] + x, pivot[1] + math.tan(math.radians(skew)) * x + scale * y


def test_the_airplane_has_both_tailplanes():
    # seen from below, as its two wings show: the one underneath is the other
    # mirrored about the fuselage, in the near wing's paint, under the fuselage
    (far_paint, far), (near_paint, near) = ha.TAILS
    assert (far_paint, near_paint) == ("hf-m", "hf-s")
    assert numbers(near) == [v if i % 2 == 0 else -v for i, v in enumerate(numbers(far))]
    plane = ha._plane()
    assert plane.index(near) < plane.index('class="hf-i"') and plane.index(far) < plane.index('class="hf-i"')
    # both inside the airplane's key and its layer
    x0, y0, x1, y1 = next(k[2] for k in ha.KEYS if k[0] == "plane")
    bx, by, bw, bh = ha.PLANE_BOX
    for d in (far, near):
        v = numbers(d)
        for x, y in zip(v[0::2], v[1::2]):
            fx, fy = ha._to_fig((x, y))
            assert x0 <= fx <= x1 and y0 <= fy <= y1
            assert bx <= fx <= bx + bw and by <= fy <= by + bh


def test_the_wings_bend_up_and_down_together_in_their_first_mode():
    px = 346 / ha.VB[2]          # a unit at a phone's width
    tips = []
    for cls, wing, _ in ha.WINGS:
        inner, _, root, cut, out, ec, et = ha._wing(wing)
        # the root reaches under the fuselage to its axis
        assert re.match(r"M-?\d+\.?\d* -?1L", inner)
        tip = (root[0] + et * out[0], root[1] + et * out[1])
        ins, outs = wing_keyframes("ha-" + cls[1:]), wing_keyframes("ha-" + cls[1:] + "o")
        want = [v for _, v, _ in ha._swings(ha.WING_P, ha._wing_env)]
        assert len(ins) == len(outs) == len(want)
        moved = []
        for (si, ki), (so, ko), w in zip(ins, outs, want):
            # the outer panel turns about the cut, then rides on the inner
            p = shear(shear(tip, cut, so, ko), root, si, ki)
            # straight up or down the picture, as far as the envelope says
            assert abs(p[0] - tip[0]) < 1e-9 and p[1] - tip[1] == pytest.approx(-w, abs=0.05)
            # the cut on a cantilever's first mode: 0.31 of the tip at 0.48 of the span
            c = shear(cut, root, si, ki)
            if abs(w) > 1:
                assert (c[1] - cut[1]) / (p[1] - tip[1]) == pytest.approx(ha._mode(ec / et), abs=0.01)
            moved.append(tip[1] - p[1])
        tips.append(moved)
    near, far = tips
    # from rest to rest, the two tips together, swing after swing the other way
    assert near[0] == near[-1] == 0 and far[0] == far[-1] == 0
    assert all(abs(n - f) < 0.1 for n, f in zip(near, far))
    swings = near[1:-1]
    assert all(p * q < 0 for p, q in zip(swings, swings[1:]))
    # 2.3 px at the most on a phone (the figure 346 px wide), never under
    # 1.2 px, and never more than a fifth of a wing's half span (the tips
    # are 46 and 48 units out from the fuselage's axis)
    size = [abs(v) for v in swings]
    assert max(size) * px >= 2.3 and min(size) * px >= 1.2
    assert max(size) <= 46 / 5
    # a slow flutter envelope: the largest swing comes as the airplane's sensor fires
    t_max = ha._swings(ha.WING_P, ha._wing_env)[1 + size.index(max(size))][0]
    assert abs(t_max - ha.FIRE["pl"]) <= ha.WING_P / 2
    assert ha._mode(0.5) == pytest.approx(0.3395, abs=1e-4)


def test_the_wings_are_layers_the_compositor_moves():
    fl = MARKUP[MARKUP.index('class="ha__m mfl"'):]
    # both wings under the fuselage, each outer panel riding on its inner one
    for cls, *_ in ha.WINGS:
        i, o = fl.index(f'class="ha__m {cls}"'), fl.index(f'class="ha__m {cls}o"')
        assert i < o < fl.index('<svg', fl.index("</span>", o))
        for c in (cls, cls + "o"):
            assert f".ha .{c}{{transform-origin:" in ha.CSS
            assert f".ha[data-live] .{c}{{animation:ha-{c[1:]} " in ha.CSS
    wings = re.findall(r"@keyframes ha-w[nf]o?\{.*?\}\}", ha.CSS)
    assert len(wings) == 4 and all(set(re.findall(r"\{(\w+)[-:]", w)) <= {"transform", "animation"}
                                   for w in wings)


# ------------------------------------------------------------------- the car

def outline(run):
    """The points of a subpath written in absolute M, L, H, V and C."""
    pts, x, y = [], 0.0, 0.0
    for op, args in re.findall(r"([MLHVCZ])([^MLHVCZ]*)", run):
        v = numbers(args)
        if op == "H":
            v = [(n, y) for n in v]
        elif op == "V":
            v = [(x, n) for n in v]
        else:
            v = list(zip(v[0::2], v[1::2]))
        for x, y in v:
            pts.append((x, y))
    return pts


def test_the_car_has_no_front():
    # it leaves to the right and comes back from the right: a car that is the
    # same both ways about its middle drives forward both times
    car = ha._car()
    mid = 1029.5
    cx = [float(v) for v in re.findall(r'cx="([\d.]+)"', car)]
    assert sorted(cx) == [mid - 37.5, mid + 37.5]
    runs = [r for d in re.findall(r' d="([^"]+)"', car) for r in re.findall(r"M[^M]+", d)]
    assert len(runs) == 4          # the body, the glass, its outline, the pillar
    for run in runs:
        pts = outline(run)
        assert [round(p[0] + q[0], 6) for p, q in zip(pts, reversed(pts))] == [2 * mid] * len(pts), run
        assert [p[1] for p in pts] == [q[1] for q in reversed(pts)] or len({p[0] for p in pts}) == 1, run
    sx, _ = ha.SENSORS["car"]
    assert abs(sx - mid) <= 0.5
    # it settles as it stops: braking that eases off (1-(1-t) cubed)
    assert ha._car_moves()[3][2] == ha.SETTLE == ".33 1 .68 1"


# ---------------------------------------------------------- always playing

def test_nothing_the_reader_does_holds_the_story():
    for text in (MARKUP, ha.CSS, ha.JS):
        assert "ha__pause" not in text and "Pause animation" not in text
    js = ha.JS
    assert "held" not in js and "btn" not in js
    # it runs whenever it is seen in a visible tab
    assert "var run=seen&&!document.hidden;" in js
    # the stylesheet pauses it only when the script says it is not running
    assert ha.CSS.count("animation-play-state:paused") == 1
    assert ".ha:not([data-run]) *{animation-play-state:paused!important}" in ha.CSS
    # a pin lights a pair; it never touches the clock
    click = js[js.index("b.addEventListener('click'"):]
    click = click[:click.index("});") + 3]
    assert "pause" not in click and "data-run" not in click
