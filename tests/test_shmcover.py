"""The SHM and NDT guide's cover, redrawn from models (round 12, shmcover).

His cover (understanding-shm-and-ndt, image1) is a drawing without words: a
small building, a wave running away from it that turns from teal to orange,
three sensor dots. tools/numfig/shm_cover.py redraws it as the waves guide's
cover does its own: the building of Figure 1 swaying in its computed first
mode with sensors on its floors, one of its steel members at the NDT scale
(an A0 guided wave from Figure 5 (a)'s model finds a defect and comes back),
and the transducer's record with the echo marked. content/anim/
anim.shmcover.json puts it where his picture stood.
"""

import html
import json
import os
import re
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))
sys.path.insert(0, os.path.join(ROOT, "tools", "numfig"))

import build  # noqa: E402
import preview  # noqa: E402

ANIM = os.path.join(ROOT, "content", "anim")
SHM = "understanding-shm-and-ndt"
NAME = "nf-shm-cover.html"
TITLE = "A building's first mode, and a guided wave's echo from a defect in one of its members"
W, H = 1000, 173                                   # his picture is 1344 x 233
BUILT = os.path.isfile(os.path.join(build.BUILD, SHM, "part-01.json"))


def page():
    with open(os.path.join(ANIM, NAME), encoding="utf-8") as fh:
        return fh.read()


def data():
    return json.loads(re.search(r"^const DATA = (\{.*\});$", page(), re.M).group(1))


def f32(s):
    import base64
    return np.frombuffer(base64.b64decode(s), dtype="<f4").astype(float)


def test_the_cover_is_a_numfig_page_in_computer_modern():
    text = page()
    assert f"<title>{html.escape(TITLE, quote=False)}</title>" in text
    assert f"const W = {W}, H = {H};" in text
    assert abs(W / H - 1344 / 233) / (1344 / 233) < 3e-3          # his picture's proportion
    # the engine is inlined and the script starts it once the type has loaded
    assert '"CMU Serif", "Figure Math"' in text and "../fonts/figure-math.woff2" in text
    assert "../fonts/cmu-serif-500-roman.woff2" in text and "function boot()" in text
    assert text.endswith("boot();\n</script>\n</body>\n</html>\n")
    low = text.lower()
    for face in ("calibri", "carlito", "cambria", "segoe ui", "arial", "helvetica", "sans-serif"):
        assert face not in low, face
    # the palette: crimson for the defect and its echo, no orange (his cover's)
    assert "#a7203a" in low and "c.accent" in low
    for warm in ("#a5510b", "#d9822b", "#f2c39a", "#fbebdd", "#7b3d0c"):
        assert warm not in low
    # our copy: no em dash, no spaced en dash, no address; type only through
    # the engine's text() and math(), never a ctx.font of its own
    assert "—" not in text and " – " not in text
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    assert "ctx.font" not in text.split("/* ---- the cover", 1)[1]


def test_its_controls_are_the_waves_covers():
    # the waves cover keeps pause and restart out of the way until a pointer
    # or the keyboard asks for them (wt_lib.QUIET_CTL), and a click still
    # pauses: not the icon's quiet mode
    import wt_lib
    text = page()
    assert wt_lib.QUIET_CTL.strip() in text
    with open(os.path.join(ANIM, "nf-wt-cover.html"), encoding="utf-8") as fh:
        assert wt_lib.QUIET_CTL.strip() in fh.read()
    assert not re.search(r"\bQUIET\s*=", text.split("/* ---- the cover", 1)[1])


def test_it_prints_its_own_frame_at_its_ratio():
    from PIL import Image
    with Image.open(os.path.join(ANIM, "nf-shm-cover.webp")) as im:
        assert im.size[0] == 1344 and abs(im.size[1] - 1344 * H / W) <= 2
        px = np.asarray(im.convert("RGB")).astype(int)
    # a frame, not a blank: the building, the plate and the record are drawn,
    # and the echo is on it in the crimson
    assert (px.mean(2) < 128).mean() > 0.01
    crimson = (abs(px[..., 0] - 0xA7) < 40) & (px[..., 1] < 90) & (px[..., 2] < 110)
    right = crimson[:, int(1344 * .75):]
    assert right.sum() > 30


def test_the_fragment_puts_it_where_his_picture_stood():
    with open(os.path.join(ANIM, "anim.shmcover.json"), encoding="utf-8") as fh:
        assert json.load(fh) == {SHM: {"image1": NAME}}
    got = preview.animations("../anim")[SHM]["image1"]
    assert got["src"] == f"../anim/{NAME}" and (got["w"], got["h"]) == (W, H)
    assert got["title"] == TITLE
    assert got["still"]["src"] == "../anim/nf-shm-cover.webp"
    # no other picture is drawn by it
    named = []
    for n in os.listdir(ANIM):
        if n == "anim.json" or re.fullmatch(r"anim\.[\w-]+\.json", n):
            with open(os.path.join(ANIM, n), encoding="utf-8") as fh:
                named += [(s, k) for s, pics in json.load(fh).items() for k, v in pics.items() if v == NAME]
    assert named == [(SHM, "image1")]


@pytest.mark.skipif(not BUILT, reason="build/ricos is written by tools/docx2ricos.py")
def test_the_document_head_shows_it_where_the_picture_stood(monkeypatch):
    monkeypatch.setattr(build, "VERBATIM", [])
    monkeypatch.setattr(build, "ANIM", {})
    before = build.page_doc(SHM)
    monkeypatch.setattr(build, "ANIM", preview.animations("../anim"))
    after = build.page_doc(SHM)
    head = lambda p: re.search(r'<header class="dochead[^"]*">(.*?)</header>', p, re.S).group(1)
    was, now = head(before), head(after)
    assert "/image1.webp" in was and "<iframe" not in was
    fig = re.search(r"<figure[^>]*>.*?</figure>", now, re.S).group(0)
    assert fig.startswith(f'<figure class="fig--anim"><iframe class="anim" src="../anim/{NAME}"')
    assert f"aspect-ratio:{W}/{H}" in fig and 'src="../anim/nf-shm-cover.webp"' in fig
    # the title, the words under it and the byline are his, unchanged
    assert re.sub(r"<figure.*?</figure>", "", was, flags=re.S) == re.sub(r"<figure.*?</figure>", "", now, flags=re.S)


def test_the_building_is_figure_1s_in_its_first_mode():
    from scipy.optimize import brentq
    d = data()
    a = d["alpha"]
    assert (d["H"], a) == (80, 6) and 1 / d["tb"] == pytest.approx(1 / 2.4, rel=1e-4)

    def char(g):                                  # Miranda and Taghavi (2005), eq. 6
        b = np.sqrt(a * a + g * g)
        return 2 + (2 + a ** 4 / (g * g * b * b)) * np.cos(g) * np.cosh(b) + a * a / (g * b) * np.sin(g) * np.sinh(b)

    gs = np.linspace(0.05, 5, 5001)
    v = char(gs)
    i = np.where(np.sign(v[:-1]) != np.sign(v[1:]))[0][0]
    g = brentq(char, gs[i], gs[i + 1], xtol=1e-14)
    b = np.sqrt(a * a + g * g)
    eta = (g * g * np.sin(g) + g * b * np.sinh(b)) / (g * g * np.cos(g) + b * b * np.cosh(b))
    xi = np.linspace(0, 1, len(d["psi"]))
    phi = np.sin(g * xi) - g / b * np.sinh(b * xi) + eta * (np.cosh(b * xi) - np.cos(g * xi))
    # the drawn shape is the closed form's, 1 at the roof, fixed at the ground, no node
    assert np.abs(np.array(d["psi"]) - phi / phi[-1]).max() < 1e-4
    assert d["psi"][0] == 0 and d["psi"][-1] == 1 and np.all(np.diff(d["psi"]) > 0)
    assert (d["hb"], d["bw"], d["storeys"]) == (136, 51, 24)


def test_the_echo_comes_back_when_the_wave_speed_says():
    import guided_ut as G
    w = data()["wave"]
    assert (w["D"], w["R"], w["f0"], w["d_mm"]) == (1.5, 0.5, 50e3, 10)
    # the group velocity of A0 at 50 kHz (the Rayleigh-Lamb root), and the echo
    # whose envelope peaks near the burst's centre + 2D/c_g (a little before:
    # dispersion, guided_ut.check.txt)
    assert w["cg_ms"] == pytest.approx(G.group_velocity("A", G.F0)[1], rel=1e-5)
    two_way = 2 * w["D"] / w["cg_ms"] * 1e6
    assert w["tof_us"] == pytest.approx(w["tpk_us"] - w["tc_us"])
    assert -0.02 < (w["tof_us"] - two_way) / two_way < 0
    # the record: the burst at the start, silence, the echo inside its window,
    # a quarter of the burst and spread out
    tr = f32(w["trace"])
    t = np.arange(len(tr)) * w["dtt_us"]
    assert len(tr) == 1401 and np.abs(tr[t < 70]).max() == pytest.approx(np.abs(tr).max())
    assert np.abs(tr[(t > 90) & (t < w["win_us"][0] - 60)]).max() < 0.01
    late = t > 600
    k = np.argmax(np.abs(tr[late]))
    assert w["win_us"][0] < t[late][k] < w["win_us"][1]
    assert 0.2 < np.abs(tr[late]).max() / np.abs(tr[t < 70]).max() < 0.35
    # the page sums the same lines the check does
    assert len(f32(w["w"])) == len(f32(w["k"])) == len(f32(w["a"])) == len(f32(w["p"])) == 353


def test_the_clock_loops_on_the_building_and_the_still_tells_it_all():
    d = data()
    w = d["wave"]
    # a wave cycle is three sways; the intro's physics starts by 0.6 s
    assert d["pw"] == pytest.approx(3 * d["tb"], rel=1e-6)
    assert d["t0b"] <= 0.6 and d["tf"] <= 0.6
    # the record, drawn as it arrives, is whole well before it fades
    assert d["tf"] + 1400e-6 * d["slow"] < d["pw"] - d["fade"] - 1
    # the still: the building at full sway, the echo's peak reaching the
    # transducer (it is on the record, named, and still in the plate)
    assert np.cos(2 * np.pi * (d["poster"] - d["t0b"]) / d["tb"]) == pytest.approx(-1, abs=1e-6)
    tm = (d["poster"] - d["tf"]) / d["slow"] * 1e6
    assert w["win_us"][0] + 60 < tm < w["win_us"][1] and abs(tm - w["tpk_us"]) < 5
    share = np.interp(tm, np.arange(len(w["share"])) * w["dth_us"], w["share"])
    assert share > 0.37                           # the arrow over the echo, at full strength
    # the plate goes quiet before the next burst
    assert w["tend_us"] * 1e-6 * d["slow"] < d["pw"] - d["fade"]


def test_the_check_file_records_the_checks_and_nothing_overlaps():
    with open(os.path.join(ROOT, "tools", "numfig", "shm_cover.check.txt"), encoding="utf-8") as fh:
        txt = fh.read()
    for n in range(1, 9):
        assert f"CHECK {n}:" in txt
    over = txt.split("OVERLAP", 1)[1].strip().splitlines()[2:]
    assert len(over) >= 8 and all(l.strip().endswith("labels none, crossings none") for l in over)
    assert "—" not in txt


def test_nothing_overlaps_across_the_motion():
    pytest.importorskip("playwright.sync_api")
    import common
    try:
        got = common.overlaps("shm-cover", [0.45, 0.8, 2.3, 3.2, 5.6, 7.5])
    except Exception as e:                        # no browser on this machine
        pytest.skip(f"playwright could not run: {e}")
    assert {k: v for k, v in got.items() if v["labels"] or v["crossings"]} == {}
