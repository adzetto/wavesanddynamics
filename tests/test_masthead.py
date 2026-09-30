"""The band across the top of the home page, and the figure that tells his sentence.

On 29 Sep 2026 the client asked for the band's wave to become a LaTeX and
manim style animation, app-like, creative, clear; then for it to be "very
stylish, clear and beautiful". site/parts/masthead.py tells his sentence in
five stages, each drawn from a model: a cable-stayed bridge built by balanced
cantilevers and swinging in its computed first mode, an atom with the de
Broglie wave five wavelengths round its orbit, the wave running on, its
samples, and the Whittaker-Shannon recovery from those very samples; then the
figure comes to rest. These hold the models to closed forms and to an
independent solution, the story to his sentence, the figure's rest to the
physics (it stops where its speed is zero), the layout's rows, and the
promises that keep it quiet: his words verbatim, the finished figure for less
motion, no clock off screen or at rest, nothing without the script but his
sentence. Nothing overlaps is checked in a browser (every formula's box
against the canvas's ink, at 24 widths from 320 to 1920px and every tenth of
a second of the story); here, the rows it relies on.
"""

import math
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

from parts import masthead as m  # noqa: E402

TAU = 2 * math.pi


def prof_header():
    src = open(os.path.join(ROOT, "site", "build.py"), encoding="utf-8").read()
    return re.search(r'PROF_HEADER = """(.*?)"""', src, re.S).group(1)


def seg(x):
    """manim's smooth, as the script has it."""
    x = min(1.0, max(0.0, x))
    return 4 * x ** 3 if x < 0.5 else 1 - (2 - 2 * x) ** 3 / 2


# ------------------------------------------------------------- the bridge

def test_the_solver_meets_the_closed_form():
    # without its stays and pylons the deck is a simply supported beam:
    # f1 = (pi / L)^2 sqrt(EI / m) / 2 pi, and its shape a half sine
    f, shape = m._deck_mode(stays=(), rests=())
    exact = (math.pi / m.SPAN) ** 2 * math.sqrt(m.EI / m.MASS) / TAU
    assert f == pytest.approx(exact, rel=1e-4)
    n = len(shape) - 1
    assert max(abs(v - math.sin(math.pi * i / n)) for i, v in enumerate(shape)) < 1e-3


def test_the_mode_is_the_models_own():
    # the same bridge by Rayleigh-Ritz, a sine series with the pylons held by
    # stiff springs, an independent method: the same frequency, the same shape
    np = pytest.importorskip("numpy")
    n_terms = 120
    j = np.arange(1, n_terms + 1)
    stiff = np.diag(m.EI * (j * np.pi / m.SPAN) ** 4 * m.SPAN / 2)

    def phi(x):
        return np.sin(j * np.pi * x / m.SPAN)

    for s, _, _, k, _ in m.STAYS:
        stiff += k * np.outer(phi(s), phi(s))
    for p in m.PYLONS:
        stiff += 1e13 * np.outer(phi(p), phi(p))
    w2, vec = np.linalg.eigh(stiff / (m.MASS * m.SPAN / 2))
    assert math.sqrt(w2[0]) / TAU == pytest.approx(m.F1, rel=2e-3)
    xs = np.arange(len(m.SHAPE)) * m.NODE
    ritz = np.sin(np.outer(xs, j) * np.pi / m.SPAN) @ vec[:, 0]
    ritz /= np.abs(ritz).max()
    if ritz[len(ritz) // 2] < 0:
        ritz = -ritz
    assert np.max(np.abs(ritz - np.array(m.SHAPE))) < 0.01


def test_the_bridge_is_built_as_one_is():
    # 150 + 350 + 150 m, stays every 20 m, each sized to carry its share of
    # the deck's weight at a stay's working stress; the first mode near half
    # a hertz, as a cable-stayed span of 350 m has it
    assert m.SPAN == 650 and m.PYLONS == (150, 500)
    assert len(m.STAYS) == 2 * (m.MAIN_STAYS + m.SIDE_STAYS)
    for s, pylon, h, k, _ in m.STAYS:
        d = abs(s - pylon)
        chord = math.hypot(d, h)
        area = k * chord / (m.E_STAY * (h / chord) ** 2)
        assert area * m.WORKING * h / chord == pytest.approx(m.MASS * m.GRAV * m.PITCH, rel=1e-9)
        assert 0 < s < m.SPAN and m.ANCHOR[0] <= h <= m.ANCHOR[1]
    assert 0.3 < m.F1 < 0.6
    # the main span's middle swings most; the pylons and the abutments stay put
    mid = len(m.SHAPE) // 2
    assert m.SHAPE[mid] == 1.0
    for p in (0, m.PYLONS[0], m.PYLONS[1], m.SPAN):
        assert m.SHAPE[int(round(p / m.NODE))] == 0.0


def test_the_deck_is_raised_by_balanced_cantilevers():
    # the deck grows out from both pylons at once, the four fronts at one
    # distance d(t) = MAIN/2 seg(...); each stay is let down as the front
    # passes its anchor (its passage the exact inverse of seg), the side spans
    # land on the abutments before the main span closes at its middle
    assert m.SIDE < m.MAIN / 2
    stays = m.DATA["stays"]
    assert len(stays) == len(m.STAYS)
    for (s, pylon, h, when), full in zip(stays, m.STAYS):
        assert (s, pylon) == (full[0], full[1])
        assert seg(when) * m.MAIN / 2 == pytest.approx(abs(s - pylon), abs=0.01)
        assert 0 < when < 1
    assert "p=seg(t,c0+D.cant[1]*st[3],.28)" in m.JS
    # the finished deck swings only once it is closed, and the atom is taken
    # from the point where it closed
    assert m.CLOSE == pytest.approx(m.STAGES[0] + sum(m.CANT))
    assert m.CLOSE < m.SWING < m.STAGES[1]
    assert m.DATA["mid"] * m.NODE == m.SIDE + m.MAIN / 2
    assert "var m=D.mid,sx=BX[m],sy=BY[m]" in m.JS


def test_the_deck_swings_in_real_time_and_rests_at_a_turn():
    # drawn at its own frequency: no slow motion to declare
    assert m.DATA["f1"] == round(m.F1, 5)
    assert "Math.sin(TAU*D.f1*s)" in m.JS
    assert len(m.DATA["shape"]) == int(m.SPAN / m.NODE) + 1
    # it comes to rest the moment it turns, where its speed is zero: sagging
    # (a positive sine moves it down the canvas), after the sweep has begun
    # and before the figure is still
    s = m.FREEZE[0] - m.SWING
    assert math.sin(TAU * m.F1 * s) == pytest.approx(1, abs=1e-6)
    assert math.cos(TAU * m.F1 * s) == pytest.approx(0, abs=2e-4)
    assert m.SWEEP < m.FREEZE[0] < m.END
    assert "Math.min(t,D.frz[0])-D.swing" in m.JS


# ------------------------------------------------------------- the atom

def test_the_orbit_holds_five_wavelengths():
    # r = r0 + a cos(n theta): n whole wavelengths round the orbit, as the
    # formula over it says, 2 pi r = 5 lambda
    assert m.QUANTUM == 5
    assert "rr=ro+a*Math.cos(D.quantum*th)" in m.JS
    assert (1, r"2\pi r=5\lambda", [(6, 7, "mh-sky")], "") in m.TAGS
    # the wave stays inside the lens, round the nucleus
    assert m.ORBIT * (1 + m.RIPPLE / m.ORBIT) < 1 and m.ORBIT * (1 - m.RIPPLE / m.ORBIT) > 0.3


def test_the_matter_wave_rests_at_its_fullest():
    # a standing wave's breath turns at its fullest: the figure holds it there
    c = math.cos(TAU * (m.FREEZE[1] - m.BREATH) / m.ATOM_PERIOD)
    assert abs(c) == pytest.approx(1, abs=1e-9)
    assert m.SWEEP < m.FREEZE[1] < m.END
    assert "Math.min(t,D.frz[1])-D.breath" in m.JS


# ------------------------------------------------------------- the signal

def recovered(width, lam, n_visible, u):
    """The script's recovery at u px from the right end, phase 0."""
    gap = lam / m.PER_WAVE
    total = 0.0
    for j in range(-m.VIRTUAL, n_visible):
        un = (j + 0.5) * gap
        z = (u - un) / gap
        total += math.sin(TAU * un / lam) * (1 if abs(z) < 1e-9 else math.sin(math.pi * z) / (math.pi * z))
    return total


def test_the_samples_are_taken_above_the_nyquist_rate():
    # T = lambda / 8 at every wavelength the strip takes: four times the rate
    assert m.PER_WAVE == 8 and m.PER_WAVE > 2
    for lo, hi, share in m.LAMBDA:
        assert 0 < lo <= hi and 0 < share < 1
    # the samples, the wave and the recovery share one phase, measured along
    # the signal from its end (u), in one row or across a phone's two
    assert "val=A*Math.sin(TAU*((n+.5)*g/L.lam+ph))" in m.JS
    assert "WY[i]=y0-A*s*Math.sin(TAU*(WU[i]/L.lam+ph))" in m.JS
    assert "WU[i]=L.wu-WX[i]" in m.JS
    assert "L.wu=2*W" in m.JS and "L.wu=W" in m.JS


def test_the_recovery_is_whittaker_shannon_from_the_samples_on_the_page():
    # it passes through every sample exactly, and between them, where the
    # wave is: at the strip's end within 0.1px, a sample's gap in within 0.1px,
    # at the recovery's first edge (no samples before the measured stretch)
    # within a pixel. The cases: a wide strip (26 samples), a phone's row (33)
    for lam, amp, n_visible, n_rec in ((160, 9, 26, 16), (80, 7, 33, 23)):
        gap = lam / m.PER_WAVE
        for j in range(n_visible):
            u = (j + 0.5) * gap
            assert recovered(0, lam, n_visible, u) == pytest.approx(math.sin(TAU * u / lam), abs=1e-12)
        for u in (0.0, 0.3 * gap, gap, 2.5 * gap):
            assert amp * abs(recovered(0, lam, n_visible, u) - math.sin(TAU * u / lam)) < 0.1
        edge = n_rec * gap
        assert amp * abs(recovered(0, lam, n_visible, edge) - math.sin(TAU * edge / lam)) < 1
    assert "s+=Math.sin(p)*z;c+=Math.cos(p)*z" in m.JS
    assert "RY[i]=y0-A*(RS[i]*c+RC[i]*s)" in m.JS


def test_the_drift_comes_to_rest_without_a_jerk():
    # one wavelength each PERIOD seconds, then from the sweep its speed falls
    # as (1 - x)^2 to nothing over DECEL, before the figure is still; the
    # phase it rests at is PHASE_END
    assert m.SWEEP + m.DECEL <= m.END
    assert "x=cl((s-se)/D.dec);return D.ph0+(se+D.dec*(1-Math.pow(1-x,3))/3)/D.P" in m.JS
    se = m.SWEEP - m.STAGES[2]
    rest = m.PHASE0 + (se + m.DECEL / 3) / m.PERIOD
    assert rest == pytest.approx(m.PHASE_END, abs=1e-12)

    def speed(x):    # d/ds of DECEL (1 - (1 - x)^3) / 3, x = s / DECEL
        return (1 - x) ** 2
    assert speed(0) == 1 and speed(1) == 0


# ------------------------------------------------------------- the story

def test_the_story_follows_his_sentence():
    # five stages in the order of his words; the first stroke within half a
    # second, the whole story in 8 to 10 seconds; each formula after its
    # stage and before the next; the sweep after the last stage has had time
    assert list(m.STAGES) == sorted(m.STAGES) and len(m.STAGES) == 5
    assert m.STAGES[0] <= 0.5 and 8 <= m.END <= 10
    for stage, at in zip(m.TAG_STAGE, m.TAG_AT):
        assert m.STAGES[stage] < m.STAGES[stage] + at < (m.STAGES + (m.SWEEP,))[stage + 1]
    assert m.STAGES[4] + 1.5 < m.SWEEP < m.END - 1
    # a told stage steps back, and all come forward again, left to right
    assert 0.3 <= m.DIM <= 0.5
    assert "if(i<4&&t>S[i+1])a=1-(1-D.dim)*seg(t,S[i+1],.6);" in m.JS
    assert "if(t>E)a+=(1-a)*seg(t,E+.1*i,.6);" in m.JS
    assert m.SWEEP + 0.1 * 4 + 0.6 <= m.END


def test_his_phrases_are_found_in_his_words():
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", prof_header()))
    for phrase in m.WORDS:
        assert text.count(phrase) == 1
    # found as ranges of his text, whitespace as it wraps, never rewritten
    assert "D.words[i].replace(/ /g,'\\\\s+')" in m.JS
    assert m.MARKS == (None, None, "masthead-wave", "masthead-dots", "masthead-data")


def test_his_phrases_hand_on_to_each_other():
    # a phrase goes out as the next comes in, over the same 0.35 s, so his
    # sentence is never without its lit phrase while the story is told
    assert "a=cl((t-S[i])/.35);b=cl(((i<4?S[i+1]:E)+.35-t)/.35);" in m.JS
    for i in range(1, m.LEVELS + 1):
        assert f"::highlight(masthead-lit{i})" in m.CSS
        assert f"::highlight(masthead-litd{i})" in m.CSS


def test_the_formulas_are_latex_set_by_mathtex():
    band = m.render()
    tags = re.findall(r'<span class="masthead__tex[^"]*" data-k="(\d)">(.*?)</span>', band)
    assert [k for k, _ in tags] == ["0", "1", "2", "2", "3", "3"]
    for _, mathml in tags:
        assert mathml.startswith("<math") and mathml.endswith("</math>") and "<wbr>" not in mathml
    assert "Masthead Math" in m.CSS and "fonts/site-math.woff2" in m.CSS
    # coloured as the figure: the recovered x-hat crimson, the samples white
    rec = tags[4][1]
    assert rec.index('class="mh-rose"') < rec.index("<mover") < rec.index('class="mh-ink"')


def test_the_formulas_stand_on_one_baseline_in_two_even_pairs():
    # each formula's baseline is found (a box of no height after it) and set
    # on its row's; the right pair's inner space is made the left pair's
    assert "g.top=L.fb[g.row]-g.el.lastChild.offsetTop" in m.JS
    assert "el.appendChild(document.createElement('i'))" in m.JS
    assert "gl=(L.ax-L.bx-L.bw/2)-(tw[0]+tw[1])/2" in m.JS
    assert "nv=Math.round((2*gl+tw[2]+tw[3])/g)" in m.JS
    # the measured widths are the long and the short sets, in the order of the tags
    long, short = m.TAG_W
    assert len(long) == len(short) == 4 and long[:2] == short[:2]
    assert long[3] > long[2] > short[2]


def test_the_formulas_have_rows_of_their_own():
    # nothing the canvas draws reaches a formula but the pylons, which the
    # bridge's formula stands between (the browser check measures that). The
    # formulas' boxes, measured in Chromium at 15px: 13px over the baseline at
    # most, 7px under it with the recovery's sum index, 1px for the atom's
    over, under, atom_under, pen = 13, 7, 1, 7
    base, (axis, axis2), (h1, h2) = m.BASE, m.AXIS, m.HIGH
    lens, lens2 = m.LENS
    assert axis - lens - 0.5 >= base + atom_under + 6          # the lens under 2 pi r = 5 lambda
    assert axis - max(m.AMP) - 1.9 >= base + under + 6         # the samples, the waves
    assert h1 >= axis + lens + 1                               # the ring, stroke and all
    # a phone: the data row's formulas clear the first row's lens by 12px, its
    # samples clear its formulas, and a pen's light on its lowest wave stays inside
    assert m.ROW2 + base - over >= axis + lens2 + 0.5 + 12
    assert axis2 - m.AMP[1] - 1.9 >= base + under + 6
    assert h2 >= m.ROW2 + axis2 + m.AMP[1] + pen
    assert f"height:{h2}px" in m.CSS and f"@container masthead (width < {m.TWO}px)" in m.CSS
    assert "two=H>1.4*D.H[0]" in m.JS


def test_a_phone_tells_it_in_two_rows():
    # the physical world in the first row, the data in the second; the
    # stylesheet decides, the script reads the strip's height and follows it
    assert m.HIGH[1] > 1.4 * m.HIGH[0]
    assert "L.y=[D.axis[0],two?D.row2+D.axis[1]:D.axis[0]]" in m.JS
    assert "if(L.two&&y>D.row2-4)return x<L.r0?3:4;" in m.JS
    # the narrowest phones set the formulas at 14px so the data row's pair keeps its room
    assert f"@container masthead (width < {m.SMALL}px)" in m.CSS and "font-size:14px" in m.CSS


def test_the_colours_on_the_navy():
    def lum(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

    def ratio(a, b):
        la, lb = sorted((lum(a), lum(b)), reverse=True)
        return (la + 0.05) / (lb + 0.05)

    sky = re.search(r"--mh-sky:(#[0-9A-F]{6})", m.CSS).group(1)
    rose = re.search(r"--mh-rose:(#[0-9A-F]{6})", m.CSS).group(1)
    for navy in ("#001C35", "#081C2F"):          # --nav-deep, light and dark themes
        assert ratio(rose, navy) >= 4.5              # "Data analytics" is set in it
        assert ratio(sky, navy) >= 4.5
    # the rose is a crimson's, not an orange's: red well above green and blue
    r, g, b = (int(rose[i:i + 2], 16) for i in (1, 3, 5))
    assert r > 200 and g < 150 and b > g - 10
    assert "accent-2" not in m.CSS


def test_line_art_on_the_pixel_grid():
    # hairlines are one device pixel; straight lines sit on the pixel grid;
    # the waves share one weight, the recovered wave a touch more
    assert "hair=1/dpr" in m.JS
    assert "function snap(v,w){var d=w*dpr;return (Math.round(v*dpr-d/2)+d/2)/dpr}" in m.JS
    assert m.LW[0] == m.LW[1] and m.LW[2] > m.LW[0]
    # nothing is cut at the strip's edges: curves end 1.5px in, pens fade before it
    assert "Math.min(W-1.5,L.w0+2*i)" in m.JS and "Math.min(W-1.5,L.r0+2*i)" in m.JS
    assert "a*=cl((W-7-x)/10)" in m.JS
    assert m.INSET >= 7


# ------------------------------------------------------- keeping it quiet

def test_his_words_go_in_verbatim():
    text = 'From elastic waves <math><mn>7</mn></math> and "numbers", <i>x</i>.'
    assert f'<p class="masthead__text">{text}</p>' in m.render(text)
    assert m.render("<p>kept</p>").count("<p>kept</p>") == 1
    assert m._HEADER == prof_header()


def test_less_motion_is_the_finished_figure_still():
    js = m.JS
    assert "if(RM)T=END;\nif(lay()){paint(T);sync()}" in js
    assert "function busy(){return !RM&&T<END}" in js
    assert m.STILL == m.END
    # the finished figure is the still: every formula has arrived and settled
    # by then, the sweep is done, the oscillations and the drift are at rest
    for stage, at in zip(m.TAG_STAGE, m.TAG_AT):
        assert m.STAGES[stage] + at + 0.45 < m.END
    assert max(m.FREEZE) < m.END and m.SWEEP + m.DECEL <= m.END
    # the story's clock is the formulas' too: nothing about them is CSS motion
    assert "transition" not in m.CSS[m.CSS.index(".masthead__tex{"):m.CSS.index(".masthead__tex math")]
    assert "g.el.style.opacity=o" in js and "g.el.style.transform=" in js


def test_no_clock_off_screen_or_in_a_hidden_tab():
    js = m.JS
    assert "vis=!document.hidden&&r.bottom>0&&r.top<innerHeight;if(!vis)halt();else if(busy())kick()" in js
    assert "document.addEventListener('visibilitychange',sync)" in js
    assert "addEventListener('scroll',soon,{passive:true})" in js
    assert "IntersectionObserver(" not in js
    # the device pixels are capped at two
    assert "dpr=Math.min(2,window.devicePixelRatio||1)" in js


def test_no_clock_at_rest():
    # the clock runs while the story is told and while the pointer's focus or
    # a stage it woke is still moving; then it stops, and nothing restarts it
    # but the pointer (there is no idle loop, no timer that draws)
    js = m.JS
    assert "if(busy()||more)raf=requestAnimationFrame(frame);else last=0;" in js
    assert "setInterval" not in js
    assert js.count("requestAnimationFrame(") == 3      # frame, kick, the scroll look
    # a woken deck or atom runs on to the end of its period, its pose in the still figure
    assert "if(h===0||X0>0){X0+=dt;if(X0>=p)X0=h===0?X0-p:0}" in js
    assert "if(h===1||X1>0){X1+=dt;if(X1>=q)X1=h===1?X1-q:0}" in js
    assert "if(T<END||RM)return false;" in js


def test_without_the_script_the_band_is_his_sentence():
    assert "html:not(.js) .masthead__wave{display:none}" in m.CSS
    band = m.render("x")
    assert 'class="masthead__wave" aria-hidden="true"' in band


def test_the_probe_reads_what_is_under_the_pointer():
    js = m.JS
    # the stage under the pointer, and the phrase under it in his words
    assert "return x<L.bx+L.bw+D.gapA[L.n]/2?0:x<L.w0+4?1:L.two||x<L.s0?2:x<L.r0?3:4;" in js
    assert "caretPositionFromPoint" in js and "caretRangeFromPoint" in js
    # on the matter wave it reads at the pointer's angle round the nucleus
    assert "th=Math.atan2(y0-PY,x-L.ax)" in js
    # a tap does it on a touch screen, and lets go
    assert js.count("setTimeout(function(){") == 2


def test_scoped_and_no_dash():
    src = open(m.__file__, encoding="utf-8").read()
    assert "\u2014" not in src and " \u2013 " not in src
    assert not re.search(r"@[A-Z0-9]+@", m.JS + m.CSS)
    # every rule's selectors are the band's (keyframe steps and the
    # highlights' pseudo-elements, named for it, aside)
    css = re.sub(r"/\*.*?\*/", "", m.CSS, flags=re.S)
    for prelude in re.findall(r"([^{};]*)\{", css):
        prelude = prelude.strip()
        if prelude.startswith("@"):
            continue
        for sel in prelude.split(","):
            sel = sel.strip()
            if sel in ("from", "to") or sel.startswith("::highlight(masthead-"):
                continue
            assert ".masthead" in sel, sel
    assert ":root" not in m.CSS
