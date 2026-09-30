"""What every figure redrawn from a numerical model shares (README.md).

build_html() writes content/anim/nf-<name>.html: the frame his animations use
(a canvas, pause and restart), the engine (engine.js), the model's numbers as
DATA, and the figure's own script. still() photographs the finished figure,
the frame print and a page without a script show, as content/anim/nf-<name>.webp.
"""

import base64
import functools
import http.server
import json
import os
import re
import shutil
import tempfile
import threading

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ANIM = os.path.join(ROOT, "content", "anim")
FONTS = os.path.join(ROOT, "content", "fonts-cmu")
DASHES = ("—", " – ")

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
@font-face{{font-family:"CMU Serif";font-style:normal;font-weight:500;font-display:block;src:url(../fonts/cmu-serif-500-roman.woff2) format("woff2")}}
@font-face{{font-family:"CMU Serif";font-style:italic;font-weight:500;font-display:block;src:url(../fonts/cmu-serif-500-italic.woff2) format("woff2")}}
@font-face{{font-family:"CMU Serif";font-style:normal;font-weight:700;font-display:block;src:url(../fonts/cmu-serif-700-roman.woff2) format("woff2")}}
@font-face{{font-family:"CMU Serif";font-style:italic;font-weight:700;font-display:block;src:url(../fonts/cmu-serif-700-italic.woff2) format("woff2")}}
@font-face{{font-family:"Figure Math";font-style:normal;font-weight:500;font-display:block;src:url(../fonts/figure-math.woff2) format("woff2")}}
html,body{{margin:0;padding:0;background:#fff;}}
.fig{{position:relative;width:100%;}}
.fig canvas{{display:block;width:100%;height:auto;cursor:pointer;}}
.ctl{{position:absolute;right:6px;bottom:6px;display:flex;gap:6px;opacity:.45;transition:opacity .2s;}}
.fig:hover .ctl,.ctl:focus-within{{opacity:1;}}
.ctl button{{width:28px;height:28px;border-radius:50%;border:1px solid #C9C4BC;background:#fff;color:#27221C;
  cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0;}}
.ctl button svg{{width:12px;height:12px;fill:currentColor;}}
.ctl #rs svg{{width:13px;height:13px;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round;}}
.ctl button:focus-visible{{outline:2px solid #095A94;outline-offset:2px;}}
/* small frames */@media (max-width:480px){{.ctl{{right:3px;bottom:3px;gap:4px;}}.ctl button{{width:22px;height:22px;}}.ctl button svg{{width:10px;height:10px;}}}}@media (max-width:300px){{#rs{{display:none;}}.ctl{{opacity:.3;}}.ctl button{{width:18px;height:18px;}}.ctl button svg{{width:8px;height:8px;}}}}
</style>
</head>
<body>
<div class="fig">
  <canvas id="c" role="img" aria-label="{aria}"></canvas>
  <div class="ctl"><button id="pp" type="button" aria-label="Pause animation"></button><button id="rs" type="button" aria-label="Restart animation"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg></button></div>
</div>
<script>
const W = {w}, H = {h};
const DATA = {data};
"""


def f32(a):
    """A float array as base64 of float32, for engine.js's b64f32()."""
    return base64.b64encode(np.ascontiguousarray(a, dtype="<f4").tobytes()).decode("ascii")


def i8(a):
    """Values already scaled to -127..127, as base64 of int8, for b64i8()."""
    return base64.b64encode(np.ascontiguousarray(np.round(a), dtype="i1").tobytes()).decode("ascii")


def _round(o, nd):
    if isinstance(o, float):
        # nd places, but a value too small for them keeps six significant
        # digits instead of rounding to nothing (1e-6 s stays 1e-6)
        if o and abs(o) < 10.0 ** (2 - nd):
            return float(f"{o:.6g}")
        return round(o, nd)
    if isinstance(o, dict):
        return {k: _round(v, nd) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_round(v, nd) for v in o]
    if isinstance(o, np.ndarray):
        return _round(o.tolist(), nd)
    if isinstance(o, np.generic):
        return _round(o.item(), nd)
    return o


def build_html(name, title, aria, w, h, data, js, digits=5):
    """Write content/anim/nf-<name>.html and return its path.

    `title` starts "Figure N: " and names the figure as his caption does;
    `aria` says in a sentence or two what the figure shows; `data` is the
    model's output (JSON-able, floats rounded to `digits` places); `js` is the
    figure's script: it defines draw() (and POSTER_T, reset(), step() if it
    needs them) and must end with boot()."""
    body = json.dumps(_round(data, digits), separators=(",", ":"))
    with open(os.path.join(HERE, "engine.js"), encoding="utf-8") as fh:
        engine = fh.read()
    page = (HEAD.format(title=title, aria=aria.replace('"', "&quot;"), w=int(w), h=int(h), data=body)
            + engine + "\n" + js.strip() + "\n</script>\n</body>\n</html>\n")
    for d in DASHES:
        if d in page:
            raise ValueError(f"nf-{name}: a dash the site does not use ({d!r})")
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", page):
        raise ValueError(f"nf-{name}: something that reads as an email address; the site's "
                         "privacy check refuses it")
    if "boot()" not in js:
        raise ValueError(f"nf-{name}: the figure's script must end with boot()")
    path = os.path.join(ANIM, f"nf-{name}.html")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    return path


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


# Ports Chrome refuses to load from (net/base/port_util.cc, ERR_UNSAFE_PORT);
# a server the system happens to put on one is closed and asked again.
_UNSAFE = {1, 7, 9, 11, 13, 15, 17, 19, 20, 21, 22, 23, 25, 37, 42, 43, 53, 69, 77, 79, 87, 95,
           101, 102, 103, 104, 109, 110, 111, 113, 115, 117, 119, 123, 135, 137, 139, 143, 161,
           179, 389, 427, 465, 512, 513, 514, 515, 526, 530, 531, 532, 540, 548, 554, 556, 563,
           587, 601, 636, 989, 990, 993, 995, 1719, 1720, 1723, 2049, 3659, 4045, 4190, 5060,
           5061, 6000, 6566, 6665, 6666, 6667, 6668, 6669, 6679, 6697, 10080}


def _server(folder):
    """An http server on a free port Chrome will load from, serving `folder`."""
    while True:
        srv = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(_Quiet, directory=folder))
        if srv.server_address[1] not in _UNSAFE:
            return srv
        srv.server_close()


def _shoot(name, shots, width):
    """Open nf-<name>.html over http beside the fonts, once per (query, png)
    in `shots`, and photograph its canvas at `width` CSS pixels, twice the
    pixels. Raises on a script error."""
    from playwright.sync_api import sync_playwright

    tmp = tempfile.mkdtemp(prefix="numfig-")
    try:
        os.makedirs(os.path.join(tmp, "anim"))
        shutil.copytree(FONTS, os.path.join(tmp, "fonts"))
        for n in os.listdir(ANIM):
            if n.startswith(f"nf-{name}") and not n.endswith(".webp"):
                shutil.copy(os.path.join(ANIM, n), os.path.join(tmp, "anim", n))
        srv = _server(tmp)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        errors = []
        with sync_playwright() as p:
            b = p.chromium.launch()
            for query, png in shots:
                pg = b.new_page(viewport={"width": width, "height": 1400}, device_scale_factor=2)
                pg.on("pageerror", lambda e: errors.append(str(e)))
                pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{name}.html?{query}")
                pg.wait_for_function("document.documentElement.dataset.ready === '1'",
                                     timeout=30000)
                pg.wait_for_timeout(200)
                pg.locator("canvas").screenshot(path=png)
                pg.close()
            b.close()
        srv.shutdown()
        if errors:
            raise RuntimeError(f"nf-{name}: script errors: {errors}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def overlaps(name, times=None, width=672):
    """Ink that collides in nf-<name>.html at its poster time and at each
    moment in `times`: {"still" or "t=<s>": {"labels": [[run, run, x, y], ...],
    "crossings": [[run, x, y], ...]}}, from engine.js's ?overlap check, with
    a PNG of each moment (the collisions outlined) in the temp directory,
    nf-<name>-overlap-<moment>.png. Labels whose ink meets are faults; a
    crossing is a dark stroke through a label, a fault unless the label sits
    on a knockout drawn after the stroke."""
    from playwright.sync_api import sync_playwright

    # times="auto": every 0.25 s up to the page's own POSTER_T (3 s at least),
    # read from the running page, since many pages compute it
    auto = times == "auto"
    tmp = tempfile.mkdtemp(prefix="numfig-")
    out = {}
    try:
        os.makedirs(os.path.join(tmp, "anim"))
        shutil.copytree(FONTS, os.path.join(tmp, "fonts"))
        shutil.copy(os.path.join(ANIM, f"nf-{name}.html"), os.path.join(tmp, "anim"))
        srv = _server(tmp)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        with sync_playwright() as p:
            b = p.chromium.launch()
            # the check works in drawing units, so one device pixel per CSS pixel
            # is enough, and a quarter of the pixels to paint per moment
            pg = b.new_page(viewport={"width": width, "height": 1400}, device_scale_factor=1)
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{name}.html?still&overlap")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            pg.wait_for_timeout(150)
            # one load, then each moment by setting the engine's clock and
            # drawing again: draw() is a pure function of t (README), so this
            # is the frame ?still&t=<s> would draw, at a fraction of the cost
            if auto:
                end = max(3.0, pg.evaluate("typeof POSTER_T === 'number' ? POSTER_T : 0"))
                steps = [.25 * j for j in range(1, int(end / .25 + .999) + 1)]
            else:
                steps = list(times or ())

            def grab(key):
                lab, cro = pg.evaluate("[window.__overlaps || [], window.__crossings || []]")
                out[key] = {"labels": lab, "crossings": cro}
                if lab or cro:
                    pg.locator("canvas").screenshot(path=os.path.join(
                        tempfile.gettempdir(), f"nf-{name}-overlap-{key.replace('=', '')}.png"))

            grab("still")
            for s in steps:
                pg.evaluate(f"() => {{ t = {s:.6g}; render(); }}")
                grab(f"t={s:g}")
            b.close()
        srv.shutdown()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def still(name, width=672, quality=92, allow=()):
    """Photograph nf-<name>.html complete (its POSTER_T, no controls) at
    `width` CSS pixels and twice the pixels, and save it beside the page as
    nf-<name>.webp: the frame print shows. Returns the path of a PNG copy to
    look at.

    Then the figure must pass the overlap check (README, "Nothing
    overlaps") at its poster and every quarter second of its motion up to
    its poster time (3 s at least): a collision raises, naming it, after the
    still is written so it can be looked at. `allow` lists what a figure
    accepts on purpose, a pair of runs ("C", "x") or a run crossed ("flaw"),
    each to be explained in its .check.txt."""
    from PIL import Image

    look = os.path.join(tempfile.gettempdir(), f"nf-{name}-still.png")
    _shoot(name, [("still", look)], width)
    with Image.open(look) as im:
        im.convert("RGB").save(os.path.join(ANIM, f"nf-{name}.webp"), "WEBP",
                               quality=quality, method=6)
    faults = collisions(name, allow, width)
    if faults:
        raise RuntimeError(f"nf-{name}: ink collides (see nf-{name}-overlap-*.png in "
                           f"{tempfile.gettempdir()}):\n  " + "\n  ".join(faults[:20]))
    return look


def collisions(name, allow=(), width=672):
    """What overlaps(), sampled at the poster and every 0.25 s up to the poster
    time (3 s at least), finds that `allow` does not excuse, as lines of text."""
    pairs = {tuple(a) for a in allow if isinstance(a, (tuple, list))}
    runs = {a for a in allow if isinstance(a, str)}
    out = []
    for when, r in overlaps(name, "auto", width).items():
        for a, b, x, y in r["labels"]:
            if (a, b) not in pairs and (b, a) not in pairs:
                out.append(f"{when}: labels {a!r} and {b!r} meet at ({x}, {y})")
        for s, x, y in r["crossings"]:
            if s not in runs:
                out.append(f"{when}: a stroke crosses {s!r} at ({x}, {y})")
    return out


def frames(name, times, width=672, out=None):
    """The figure at each moment in `times` (seconds of its clock), as PNGs
    in `out` (default: the temp directory): to see that the motion is right.
    Returns their paths."""
    out = out or tempfile.gettempdir()
    shots = [(f"still&t={t:g}", os.path.join(out, f"nf-{name}-t{t:g}.png")) for t in times]
    _shoot(name, shots, width)
    return [png for _, png in shots]
