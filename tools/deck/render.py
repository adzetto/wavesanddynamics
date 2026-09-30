"""Render the deck's slides from their sources: tools/deck/src/<stem>.html (+ <stem>.py).

    python tools/deck/render.py 4            render slide 4, check it, and write
                                             content/deck-probstat/s004.png and
                                             web/s004-{1600,960,320}.webp (and its
                                             animation, anim/s004.html, if it has one)
    python tools/deck/render.py 7a 65a       slides of ours go by their labels
    python tools/deck/render.py 1-8 12       several; a range runs in the deck's
                                             order, so 7-8 holds 7a, 7b ... too
    python tools/deck/render.py 9-16 --look  render and check only: nothing in
                                             content/ changes (to iterate)
    python tools/deck/render.py --vector     the deck as vectors (below), from the
                                             slides as they stand: the controller
                                             runs this once, when every agent is done
    python tools/deck/render.py 4 --vector   write slide 4, then print the vectors
    python tools/deck/render.py --manifest   write deck.json again from the slides
                                             in content/ (the deck in order)
    python tools/deck/render.py --sheet      a contact sheet of the deck as it
                                             stands, build/r10-deck/review/sheet-*.png

The deck's labels (his.py): his slides keep his numbers, a slide of ours is
lettered after the one it follows (65a, 7a). A slide's files are named by its
stem, s004 or s065a, in src/, in content/deck-probstat/ and in the review.

Each slide is assembled (its figures computed, his formulas typeset), opened
in Chromium at 1920 x 1080 and photographed at twice the pixels. Every copy is
brought down from that master with Lanczos, never up: the 1920 PNG the deck
keeps, and the three the site publishes, <stem>-1600.webp (quality 70),
<stem>-960.webp (60) and <stem>-320.webp (50), at WebP's slowest, smallest
setting, as site/parts/deck.py describes them.

The checks (a slide that fails one is not written to content/ unless --force):
  his words   the slide's text, read back from the page, is his and all of
              his: every paragraph his file holds for the slide (his.py), and
              the words he drew into his pictures (src/<stem>.pic.txt), each
              appears whole; no word appears that is not his. Compared after
              Unicode's compatibility normalisation (mathtype.norm): his "σ²"
              is our σ with a superscript 2. Tick numbers are data, exempt.
              A slide of ours (his.OURS) has no words of his: its own keep the
              site's rules (no em dash, no spaced en dash) and its running
              foot ends in its label. Where his file cannot be read
              (DECK_PPTX), the check says so, and the slide is written only
              with --force.
  overflow    nothing leaves the page or its box, the body stays clear of the
              foot, no text sits on other text
  legible     text 24 px or larger on the 1920 slide (12 px in the 960 copy),
              the running foot and tick numbers 22 px or larger; a slide may
              lower its own floor with data-min (the map, 20; references, 22)
  leading     text that runs to two lines is set at 1.3 or more; a title or a
              heading of 30 px and up may be tighter
  animation   (a slide whose script sets ANIM, DECK_BRIEF.md "Animated slides")
              its page (anim/<stem>.html) runs without a script error, its
              last frame is the slide's photograph (ANIM_TOL), it plays to its
              end and stops, it shows the slide at once to a reader who asks
              for less motion, and every animated value ends where the slide
              has it. Its frames are written to look at: review/<stem>-anim-
              <t>.png and the sheet review/<stem>-anim.png.
Also written, to look at: build/r10-deck/review/<stem>.png (his slide and ours
side by side at 960; a slide of ours between the deck's slides either side of
it), <stem>-960.png (ours as the page's 960 copy shows it), <stem>.json (the
report) and build/r10-deck/slides/<stem>.html (the page itself).

The manifest, content/deck-probstat/deck.json: the deck in order, a slide a
line with its label, stem and title (and "anim", its length in seconds, when
it has an animation). A slide joins it, or has its line brought up to date,
when it is written; site/build.py and the presenter read it.

The deck as vectors (vector.py), with --vector: every slide printed by
Chromium into one PDF (his words stay text, the figures paths), content/
deck-probstat/probability-statistics-and-estimation.pdf, which the site offers
for download, and each page as an SVG, web/<stem>.svg, which the viewer shows
while presenting, sharp at any size. Both are written only when every page and
every SVG agree with the slide's photograph (VEC_TOL) and the PDF is under
3 MB; build/r10-deck/review/vector.json has the figures.

Several agents render at once (DECK_BRIEF.md "Rendering side by side"). What
belongs to one slide (its photograph, its web copies, its animation page, its
review files) is written whole or not at all: to a temporary file, then
renamed into place. What the deck shares is written under a lock in
build/r10-deck/locks/: the manifest (a line changed, the file replaced whole),
the animation pages' shared files, and the vector print, which a plain write
never starts: the controller prints once, at the end.
"""

import argparse
import collections
import contextlib
import functools
import html as _html
import http.server
import importlib.util
import io
import json
import os
import re
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
# a slide's script may borrow a figure from another's: from s002 import demand_capacity
sys.path.insert(1, os.path.join(HERE, "src"))

import his  # noqa: E402
import mathtype  # noqa: E402
import vector  # noqa: E402

SRC = os.path.join(HERE, "src")
DECK = os.path.join(ROOT, "content", "deck-probstat")
ORIG = os.path.join(DECK, "_orig")
BUILD = os.path.join(ROOT, "build", "r10-deck")
MANIFEST = os.path.join(DECK, "deck.json")
ANIM = os.path.join(DECK, "anim")            # the animation pages the site publishes
ANIM_LOOK = os.path.join(BUILD, "anim")      # the same, while iterating (--look)
WEB = ((1600, 70), (960, 60), (320, 50))
# the deck as vectors (vector.py): the PDF the site offers for download, and
# the name, author and page count it carries
PDF_NAME = "probability-statistics-and-estimation.pdf"
DECK_TITLE = "Probability, statistics and estimation"
AUTHOR = "Korkut Kaynardag"
COUNT = his.COUNT          # his 73 slides and ours (his.OURS)
# the most a vector copy may differ from its slide's photograph: the largest
# difference (0 to 255) once both are blurred over 9 px, where anti-aliasing
# washes out and a moved or missing mark does not (the deck measures 20 to
# 40; a label printed out of its place measured over 100)
VEC_TOL = 60
# the same measure for an animation's last frame against the photograph: it
# is the same page, so anything but anti-aliasing is a mark out of place
ANIM_TOL = 12
FILE_MAX = 3_000_000        # the site's limit for one file (site/build.py)
MIN_PX, MIN_RUN_PX, MIN_TICK_PX = 24, 22, 22
NUMERIC = re.compile(r"^[\s0-9.,−\-+%×·()10⁰¹²³⁴⁵⁶⁷⁸⁹⁻/]*$")
# The fonts deck.css names, and where the site publishes them: its root's
# fonts/ folder (site/build.py copies site/fonts and content/fonts-cmu there,
# and the deck's Latin Modern Math subset with the animations). An animation
# page is three folders down (deck/probability/anim/ on the site,
# content/deck-probstat/anim/ here), so it reaches them as ../../../fonts/;
# this script's own server answers /fonts/ from the same three folders.
FONT_DIRS = (os.path.join(ROOT, "site", "fonts"), os.path.join(ROOT, "content", "fonts-cmu"),
             os.path.join(HERE, "fonts"))
FONT_URL = re.compile(r"url\(/(?:site/fonts|content/fonts-cmu|tools/deck/fonts)/([\w.-]+\.woff2)\)")

SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Slide {n}</title>
<link rel="stylesheet" href="/tools/deck/deck.css">
</head>
<body>
{body}
<script src="/tools/deck/deck.js"></script>
</body>
</html>
"""

# An animated slide's own page (DECK_BRIEF.md "Animated slides"): the slide as
# it is rendered, and beside it, by relative paths, the deck's stylesheet (its
# fonts from the site's), deck.js (the wires) and the runtime, anim.js. The
# slide stays hidden until the runtime has drawn its first frame.
ANIM_SHELL = """<!DOCTYPE html>
<html lang="en" class="anim-page anim-wait">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{title}</title>
<link rel="stylesheet" href="deck.css">
<style>html.anim-page,html.anim-page body{{width:100%;height:100%;overflow:hidden;background:#fff}}
html.anim-page .slide{{transform-origin:0 0}}
html.anim-wait .slide{{visibility:hidden}}</style>
</head>
<body>
{body}
<script type="application/json" id="deck-anim">{config}</script>
<script src="deck.js"></script>
<script src="anim.js"></script>{hook}
</body>
</html>
"""

FIG = re.compile(r'<div\s+data-fig="([\w-]+)"([^>]*)>\s*</div>')


# ------------------------------------------------------------------ labels

def slides(args):
    """The labels named by args, in the deck's order: a label (4, 7a), a
    range between two labels (1-8, 60-66, 7a-7c: everything from the one to
    the other in the deck's order), or all."""
    out = set()
    for a in args:
        a = str(a).strip().lower()
        if a == "all":
            out.update(his.LABELS)
            continue
        m = re.fullmatch(r"(\d+[a-z]*)-(\d+[a-z]*)", a)
        try:
            if m:
                lo, hi = his.LABELS.index(his.label(m.group(1))), his.LABELS.index(his.label(m.group(2)))
                out.update(his.LABELS[lo:hi + 1])
            else:
                out.add(his.label(a))
        except ValueError as e:
            raise SystemExit(f"not a slide or a range of the deck: {a} ({e})")
    return [lab for lab in his.LABELS if lab in out]


def src(label, ext):
    return os.path.join(SRC, his.stem(label) + ext)


def module(label):
    path = src(label, ".py")
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location(f"deck_{his.stem(label)}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def slide_body(label, html_path=None, mod=None):
    """The slide's <section>: its figures computed and put in, his formulas set."""
    name = html_path or src(label, ".html")
    with open(name, encoding="utf-8") as fh:
        body = fh.read()
    mod = mod or (module(label) if html_path is None else None)
    stem = os.path.splitext(os.path.basename(name))[0]

    def fig(mo):
        fn = mo.group(1)
        if mod is None or not hasattr(mod, fn):
            raise SystemExit(f"{stem}: data-fig=\"{fn}\" but src/{stem}.py has no {fn}()")
        out = getattr(mod, fn)()
        extra = mo.group(2).strip()
        if extra:  # keep the placeholder's class/id/style/data-in on a wrapper
            return f"<div {extra}>{out}</div>"
        return out

    body = FIG.sub(fig, body)
    return mathtype.expand(body)


def assemble(label, html_path=None, mod=None):
    """The slide's page: its section alone at 1920 x 1080."""
    return SHELL.format(n=label, body=slide_body(label, html_path, mod))


def title_of(label):
    """The slide's title as text: its <h1>, the tags taken out (his words;
    the viewer's alt text and the PDF's bookmark)."""
    with open(src(label, ".html"), encoding="utf-8") as fh:
        page = fh.read()
    m = re.search(r'<h1 class="title[^"]*">(.*?)</h1>', page, re.S)
    return " ".join(_html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).split()) if m else ""


def pic_words(label):
    path = src(label, ".pic.txt")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [ln.rstrip("\n") for ln in fh if ln.strip() and not ln.startswith("#")]


# our own words keep the site's rules (site/build.py --strict): no em dash,
# no spaced en dash
OUR_DASH = re.compile(r"—|\s–\s")


def check(label, info):
    """His words (or, on a slide of ours, our rules), overflow and size.
    Returns a list of problems."""
    probs = list(info["problems"])
    ours_blocks = [(mathtype.norm(b["t"]), b) for b in info["blocks"]]
    ticks = [t for t, b in ours_blocks if b["tick"]]
    words = [t for t, b in ours_blocks if not b["tick"] and t]
    if his.his(label) is None:
        for b in info["blocks"]:
            if OUR_DASH.search(b["t"]):
                probs.append(f"a dash our copy may not have: \"{b['t'].strip()[:40]}\"")
        runs = [t for t, b in ours_blocks if b["run"] and t]    # .map, .src, .num
        if not runs or runs[-1] != label:
            probs.append(f"the running foot does not end in the slide's label {label}")
        if pic_words(label):
            probs.append(f"src/{his.stem(label)}.pic.txt lists his words, but slide {label} is ours")
    else:
        try:
            strings = his.strings(label)
        except (ImportError, OSError) as e:
            # his PowerPoint is read, never published: on a machine without
            # it (DECK_PPTX) his words cannot be held to it, and the slide is
            # not written unless --force says so
            probs.append(f"his words not checked: his PowerPoint cannot be read here ({type(e).__name__}: {e})")
            strings = None
    if his.his(label) is not None and strings is not None:
        theirs = [mathtype.norm(s) for s in strings + pic_words(label)]
        flat = " ".join(words)
        for s in theirs:
            if s and s not in flat:
                probs.append(f"his words missing or broken: \"{s}\"")
        want = collections.Counter(w for s in theirs for w in s.split())
        have = collections.Counter(w for s in words for w in s.split())
        extra, short = have - want, want - have
        if extra:
            probs.append("words that are not his: " + ", ".join(f"{w!r}x{k}" for w, k in extra.items()))
        if short:
            probs.append("his words not on the slide: " + ", ".join(f"{w!r}x{k}" for w, k in short.items()))
    for t in ticks:
        if not NUMERIC.match(t):
            probs.append(f"a tick label that is not a number: {t!r}")
    floor = info.get("min")          # the one dense slide may set its own (data-min)
    small = [(b["px"], mathtype.norm(b["t"])[:40]) for b in info["blocks"]
             if b["px"] < (floor or (MIN_TICK_PX if b["tick"] else MIN_RUN_PX if b["run"] else MIN_PX))]
    for px, t in small:
        probs.append(f"too small to read at 960: {px:g}px \"{t}\"")
    if any(b.get("transform", "none") != "none" for b in info["blocks"]):
        probs.append("text-transform changes his characters")
    return probs


# ------------------------------------------------------------------ side by side

@contextlib.contextmanager
def lock(name, wait=1800.0, stale=3600.0):
    """Hold build/r10-deck/locks/<name>.lock while the block runs: another
    render.py that wants the same lock waits for it. A lock older than
    `stale` seconds was left by a run that died, and is taken over."""
    path = os.path.join(BUILD, "locks", name + ".lock")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    t0, said = time.time(), False
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(path) > stale:
                    os.remove(path)
                    continue
            except OSError:
                continue
            if time.time() - t0 > wait:
                raise SystemExit(f"{name}: {path} is held by another render.py (waited {wait:.0f} s)")
            if not said:
                print(f"{name}: waiting for another render.py ({os.path.relpath(path, ROOT)})")
                said = True
            time.sleep(0.4)
            continue
        with os.fdopen(fd, "w") as fh:
            fh.write(f"{os.getpid()} {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        break
    try:
        yield
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _replace(tmp, path):
    """Rename tmp over path; a reader holding path open (a site build copying
    it, on Windows) gets a moment to let go."""
    for k in range(40):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.05 * (k + 1))
    os.replace(tmp, path)


def write_file(path, data):
    """Write path whole or not at all: a temporary file beside it, renamed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "wb") as fh:
        fh.write(data.encode("utf-8") if isinstance(data, str) else data)
    _replace(tmp, path)


def save_image(im, path, fmt, **kw):
    """A picture saved whole or not at all (PIL, then renamed)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    im.save(tmp, fmt, **kw)
    _replace(tmp, path)


def write_if_changed(path, data):
    """Write path only if its content differs (shared files: two runs that
    write the same bytes never race to a half-written file)."""
    b = data.encode("utf-8") if isinstance(data, str) else data
    try:
        with open(path, "rb") as fh:
            if fh.read() == b:
                return False
    except OSError:
        pass
    write_file(path, b)
    return True


# ------------------------------------------------------------------ the manifest

def manifest():
    """deck.json: the deck in order, [{label, stem, title[, anim]}], or []."""
    try:
        with open(MANIFEST, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return []


def _dump_manifest(rows):
    return "[\n" + ",\n".join(" " + json.dumps(r, ensure_ascii=False) for r in rows) + "\n]\n"


def update_manifest(rows):
    """Bring the manifest's lines for these slides up to date ({label: row}),
    under the lock: read, change, write whole. Lines stay in the deck's order;
    a label the deck no longer has (his.LABELS) is dropped."""
    with lock("manifest", wait=120, stale=300):
        have = {r["label"]: r for r in manifest()}
        have.update(rows)
        out = [have[lab] for lab in his.LABELS if lab in have]
        write_if_changed(MANIFEST, _dump_manifest(out))
    return out


def rebuild_manifest():
    """The manifest from the slides content/ holds, in the deck's order."""
    rows = {}
    for lab in his.LABELS:
        stem = his.stem(lab)
        if not os.path.isfile(os.path.join(DECK, f"{stem}.png")):
            continue
        rows[lab] = row(lab, anim_length(os.path.join(ANIM, f"{stem}.html")))
    with lock("manifest", wait=120, stale=300):
        out = [rows[lab] for lab in his.LABELS if lab in rows]
        write_if_changed(MANIFEST, _dump_manifest(out))
    missing = [lab for lab in his.LABELS if lab not in rows]
    print(f"manifest: {len(out)} slides in {os.path.relpath(MANIFEST, ROOT)}"
          + (f"; not written yet: {' '.join(missing)}" if missing else ""))
    return out


def row(label, anim=None):
    r = {"label": label, "stem": his.stem(label), "title": title_of(label)}
    if anim:
        r["anim"] = anim
    return r


def anim_length(path):
    """An animation page's length in seconds, from its config, or None."""
    try:
        with open(path, encoding="utf-8") as fh:
            m = re.search(r'<script type="application/json" id="deck-anim">(.*?)</script>', fh.read(), re.S)
        return json.loads(m.group(1)).get("length") if m else None
    except OSError:
        return None


# ------------------------------------------------------------------ the server

class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def translate_path(self, path):
        # /fonts/<name>: the site's fonts folder, as an animation page reaches it
        m = re.match(r"/fonts/([\w.-]+)$", path.split("?", 1)[0])
        if m:
            for d in FONT_DIRS:
                p = os.path.join(d, m.group(1))
                if os.path.isfile(p):
                    return p
        return super().translate_path(path)


@functools.lru_cache(maxsize=1)
def server():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}"


INFO_JS = "() => deckInfo()"
# The faces the slide's words are set in (each style and weight of each first
# family a piece of text asks for), and any of them that is not loaded: a
# photograph taken with a fallback face is refused. A face no text uses is not
# asked for (an italic nothing on the slide is set in never loads).
FACES_JS = """() => {
  const used = new Set(), walk = document.createTreeWalker(document.querySelector('.slide'), NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walk.nextNode())) {
    if (!n.nodeValue.trim() || n.parentElement.closest('script,style')) continue;
    const cs = getComputedStyle(n.parentElement);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const fam = cs.fontFamily.split(',')[0].trim().replace(/^["']|["']$/g, '');
    used.add((cs.fontStyle === 'italic' ? 'italic ' : '') + cs.fontWeight + ' 24px "' + fam + '"');
  }
  return [...used].filter(f => !document.fonts.check(f)).sort();
}"""


# ------------------------------------------------------------------ animation pages

def anim_css():
    """deck.css for the animation pages: its fonts from the site's fonts/."""
    with open(os.path.join(HERE, "deck.css"), encoding="utf-8") as fh:
        css = fh.read()
    return FONT_URL.sub(lambda m: f"url(../../../fonts/{m.group(1)})", css)


def anim_fonts():
    """The font files the animation pages name (the site publishes them)."""
    return sorted(set(FONT_URL.findall(open(os.path.join(HERE, "deck.css"), encoding="utf-8").read())))


def anim_assets(folder):
    """The files every animation page in `folder` shares: deck.css (its
    fonts from the site's), deck.js and anim.js. Written under the lock, and
    only when they differ."""
    with lock("anim-assets", wait=120, stale=300):
        write_if_changed(os.path.join(folder, "deck.css"), anim_css())
        for f in ("deck.js", "anim.js"):
            with open(os.path.join(HERE, f), encoding="utf-8") as fh:
                write_if_changed(os.path.join(folder, f), fh.read())


def anim_page(label, body, mod):
    """An animated slide's own page (ANIM_SHELL), or None if its script sets
    no ANIM. The config the runtime reads is ANIM, with the slide's label and
    stem; ANIM_JS, if the script has it, is the slide's own hook."""
    cfg = getattr(mod, "ANIM", None) if mod else None
    if cfg is None:
        return None
    cfg = dict(cfg, label=label, stem=his.stem(label))
    hook = getattr(mod, "ANIM_JS", "") or ""
    title = title_of(label)
    return ANIM_SHELL.format(
        title=_html.escape(f"Slide {label}: {title}" if title else f"Slide {label}", quote=False),
        body=body, config=json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/"),
        hook=f"\n<script>\n{hook.strip()}\n</script>" if hook.strip() else "")


def _settled(pg):
    pg.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")


def anim_check(b, label, url, master):
    """Open the animation page and check it (the docstring's "animation").
    Returns (problems, info): its report, and the frames written."""
    from PIL import Image
    stem = his.stem(label)
    probs, errors, info = [], [], {}

    def watch(pg):
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        return pg
    ready = "document.documentElement.dataset.anim === 'ready'"
    # the last frame, photographed as the slide is, against its photograph
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
    pg = watch(ctx.new_page())
    pg.goto(f"{url}?t=end")
    pg.wait_for_function(ready, timeout=30000)
    rep = pg.evaluate("() => DeckAnim.report()")
    _settled(pg)
    with Image.open(io.BytesIO(pg.screenshot())) as im:
        last = im.convert("RGB").resize((1920, 1080), Image.LANCZOS)
    with Image.open(master) as im:
        photo = im.convert("RGB").resize((1920, 1080), Image.LANCZOS)
    worst = _worst(photo, last)
    info["last_frame"] = worst
    if worst > ANIM_TOL:
        probs.append(f"the animation's last frame differs from the photograph ({worst} > {ANIM_TOL})")
    ctx.close()
    probs += [f"animation: {p}" for p in rep.get("problems", [])]
    for g in rep.get("ghostText", []):
        if his.his(label) is not None and not NUMERIC.match(mathtype.norm(g)):
            probs.append(f"animation: a word shown only while it plays is not his: {g!r}")
    info.update({k: rep.get(k) for k in ("length", "end", "actors", "cues")})
    info["schedule"] = rep.get("schedule")
    # frames to look at, and a sheet of them
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
    pg = watch(ctx.new_page())
    pg.goto(f"{url}?t=0")
    pg.wait_for_function(ready, timeout=30000)
    length = float(rep.get("length") or 0)
    moments = sorted({round(length * k / 11, 2) for k in range(12)} |
                     {round(float(t), 2) for t in (rep.get("frames") or [])})
    for old in os.listdir(os.path.join(BUILD, "review")):
        if old.startswith(f"{stem}-anim-") and old.endswith(".png"):
            os.remove(os.path.join(BUILD, "review", old))
    shots = []
    for t in moments:
        pg.evaluate("t => DeckAnim.seek(t)", t)
        _settled(pg)
        with Image.open(io.BytesIO(pg.screenshot())) as im:
            fr = im.convert("RGB").resize((960, 540), Image.LANCZOS)
        p = os.path.join(BUILD, "review", f"{stem}-anim-{t:05.2f}.png")
        fr.save(p)
        shots.append((t, fr))
    info["frames"] = [t for t, _ in shots]
    anim_sheet(stem, shots)
    # played through (eight times as fast): it reaches its end and stops
    pg.goto(f"{url}?speed=8")
    try:
        pg.wait_for_function("window.DeckAnim && DeckAnim.state === 'done'",
                             timeout=int(length / 8 * 1000) + 15000)
        pg.wait_for_timeout(300)
        run = pg.evaluate("() => ({running: DeckAnim.running, frames: DeckAnim.frames, "
                          "slowest: DeckAnim.slowest})")
        info["played"] = run
        if run["running"]:
            probs.append("animation: still asking for frames after its end")
    except Exception:  # noqa: BLE001 (a timeout: it never ended)
        probs.append("animation: it did not reach its end when played")
    ctx.close()
    # a reader who asks for less motion: the slide at once
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2,
                        reduced_motion="reduce")
    pg = watch(ctx.new_page())
    pg.goto(url)
    pg.wait_for_function(ready, timeout=30000)
    _settled(pg)
    if pg.evaluate("() => DeckAnim.state") != "done":
        probs.append("animation: with less motion asked for, the slide is not shown at once")
    with Image.open(io.BytesIO(pg.screenshot())) as im:
        still = im.convert("RGB").resize((1920, 1080), Image.LANCZOS)
    w = _worst(photo, still)
    if w > ANIM_TOL + 20:            # a 1x screenshot against the 2x photograph
        probs.append(f"animation: with less motion asked for, the page differs from the slide ({w})")
    ctx.close()
    probs += [f"animation, script: {e}" for e in dict.fromkeys(errors)]
    return probs, info


def anim_sheet(stem, shots, cols=4, w=480):
    """The frames of an animation on one sheet, each with its moment."""
    from PIL import Image, ImageDraw
    h = w * 9 // 16
    rows = (len(shots) + cols - 1) // cols
    M = Image.new("RGB", (cols * (w + 12), rows * (h + 30)), "#9a958d")
    d = ImageDraw.Draw(M)
    for k, (t, fr) in enumerate(shots):
        x, y = (k % cols) * (w + 12), (k // cols) * (h + 30)
        M.paste(fr.resize((w, h), Image.LANCZOS), (x, y + 24))
        d.text((x + 4, y + 6), f"t = {t:.2f} s", fill="#ffffff")
    save_image(M, os.path.join(BUILD, "review", f"{stem}-anim.png"), "PNG")


# ------------------------------------------------------------------ rendering

def shoot(labels, look_only=False, force=False, with_anim=True):
    """Open each assembled slide, photograph it, check it (and its
    animation), and write it. Returns (problems, room, written rows)."""
    from PIL import Image
    from playwright.sync_api import sync_playwright

    for d in ("slides", "review"):
        os.makedirs(os.path.join(BUILD, d), exist_ok=True)
    base = server()
    report, room, rows, anims = {}, {}, {}, {}
    with sync_playwright() as p:
        # grayscale anti-aliasing and unhinted outlines: the same glyphs at every size
        b = p.chromium.launch(args=["--disable-lcd-text", "--font-render-hinting=none"])
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        for lab in labels:
            stem = his.stem(lab)
            errors = []
            pg = ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            pg.goto(f"{base}/build/r10-deck/slides/{stem}.html")
            pg.wait_for_function("window.DECK_READY === true", timeout=30000)
            faces = pg.evaluate(FACES_JS)
            master = os.path.join(BUILD, "slides", f"{stem}@2x.png")
            pg.screenshot(path=master, clip={"x": 0, "y": 0, "width": 1920, "height": 1080})
            info = pg.evaluate(INFO_JS)
            pg.close()
            probs = check(lab, info)
            if faces:
                probs.append(f"fonts not loaded: {faces}")
            probs += [f"script: {e}" for e in errors]
            # its animation, from the preview folder; written to content/ with the slide
            page = os.path.join(ANIM_LOOK, f"{stem}.html")
            if with_anim and os.path.isfile(page):
                ap, ainfo = anim_check(b, lab, f"{base}/build/r10-deck/anim/{stem}.html", master)
                probs += ap
                anims[lab] = ainfo
            report[lab] = probs
            room[lab] = info.get("room")
            with Image.open(master) as im:
                im = im.convert("RGB")
                full = im.resize((1920, 1080), Image.LANCZOS)
                ours960 = im.resize((960, 540), Image.LANCZOS)
                # his and ours side by side, as the page's 960 copy shows them;
                # a slide of ours has no original, so it is shown between the
                # deck's slides before and after it
                h = his.his(lab)
                k = his.LABELS.index(lab)
                near = [his.LABELS[j] for j in (k - 1, k + 1) if 0 <= j < len(his.LABELS)]
                sides = ([os.path.join(ORIG, f"s{h:03d}.png")] if h else
                         [os.path.join(DECK, f"{his.stem(x)}.png") for x in near])
                sheet_ = Image.new("RGB", (1940 if h else 2920, 540), "#9a958d")
                for j, op in enumerate(sides):
                    if os.path.isfile(op):
                        with Image.open(op) as o:
                            sheet_.paste(o.convert("RGB").resize((960, 540), Image.LANCZOS),
                                         (0 if j == 0 else 1960, 0))
                sheet_.paste(ours960, (980, 0))
                save_image(sheet_, os.path.join(BUILD, "review", f"{stem}.png"), "PNG")
                save_image(ours960, os.path.join(BUILD, "review", f"{stem}-960.png"), "PNG")
                if look_only or (probs and not force):
                    continue
                save_image(full, os.path.join(DECK, f"{stem}.png"), "PNG", optimize=True)
                for w, q in WEB:
                    save_image(im.resize((w, w * 9 // 16), Image.LANCZOS),
                               os.path.join(DECK, "web", f"{stem}-{w}.webp"), "WEBP", quality=q, method=6)
            # the animation page goes with the slide; a slide that lost its
            # animation loses its page
            live = os.path.join(ANIM, f"{stem}.html")
            if os.path.isfile(page) and with_anim:
                anim_assets(ANIM)
                with open(page, encoding="utf-8") as fh:
                    write_file(live, fh.read())
            elif os.path.isfile(live) and with_anim:
                os.remove(live)
            rows[lab] = row(lab, anim_length(live) if os.path.isfile(live) else None)
        b.close()
    return report, room, rows, anims


def kit():
    """The sampler (kit.html, kit.py): every component once, to look at."""
    from playwright.sync_api import sync_playwright
    spec = importlib.util.spec_from_file_location("deck_kit", os.path.join(HERE, "kit.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    os.makedirs(os.path.join(BUILD, "slides"), exist_ok=True)
    os.makedirs(os.path.join(BUILD, "review"), exist_ok=True)
    write_file(os.path.join(BUILD, "slides", "kit.html"),
               assemble("kit", os.path.join(HERE, "kit.html"), mod))
    out = os.path.join(BUILD, "review", "kit.png")
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--disable-lcd-text", "--font-render-hinting=none"])
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.goto(f"{server()}/build/r10-deck/slides/kit.html")
        pg.wait_for_function("window.DECK_READY === true", timeout=30000)
        pg.screenshot(path=out)
        b.close()
    print(out)


def sheet(cols=4, w=480, drawn=False):
    """The deck as it stands, 24 slides to a sheet, each with its label: the
    photographs, or (drawn) each slide's SVG as Chromium drew it in the last
    --vector."""
    from PIL import Image, ImageDraw
    os.makedirs(os.path.join(BUILD, "review"), exist_ok=True)
    h = w * 9 // 16
    labels = [lab for lab in his.LABELS if os.path.isfile(os.path.join(DECK, f"{his.stem(lab)}.png"))]
    for part, lo in enumerate(range(0, len(labels), 24)):
        ids = labels[lo:lo + 24]
        rows = (len(ids) + cols - 1) // cols
        M = Image.new("RGB", (cols * (w + 12), rows * (h + 12)), "#9a958d")
        d = ImageDraw.Draw(M)
        for k, lab in enumerate(ids):
            stem = his.stem(lab)
            src_ = (os.path.join(BUILD, "vec", f"{stem}-960.png") if drawn
                    else os.path.join(DECK, f"{stem}.png"))
            if not os.path.isfile(src_):
                continue
            with Image.open(src_) as im:
                x, y = (k % cols) * (w + 12), (k // cols) * (h + 12)
                M.paste(im.convert("RGB").resize((w, h), Image.LANCZOS), (x, y))
                d.text((x + 6, y + 4), lab, fill="#c00")
        path = os.path.join(BUILD, "review", f"{'vector-' if drawn else ''}sheet-{part + 1}.png")
        save_image(M, path, "PNG")
        print(path)


def _worst(a, b, radius=4):
    """The largest difference after a box blur of `radius` px."""
    from PIL import ImageChops, ImageFilter
    return ImageChops.difference(a, b).convert("L").filter(ImageFilter.BoxBlur(radius)).getextrema()[1]


# a page that shows one SVG as the viewer does, in an <img>, at slide size
VIEW = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>SVG</title>
<style>html,body{margin:0;background:#fff}img{display:block;width:1920px;height:1080px}</style>
</head><body><img alt=""><script>document.querySelector('img').src=location.search.slice(1)</script>
</body></html>
"""


def vectors(force=False):
    """The deck as vectors (vector.py), under the vector lock. Every slide
    goes on one page, in the deck's order, which Chromium prints to a PDF;
    the PDF is tidied and each of its pages cut into an SVG. Every page (as
    MuPDF draws it) and every SVG (as Chromium draws it, in an <img> at twice
    the pixels, brought down as the photographs are) is held against the
    slide's photograph; only when all agree, and the PDF is under the site's
    3 MB a file, are content/deck-probstat/<PDF_NAME> and web/<stem>.svg
    written. The SVGs as drawn stay in build/r10-deck/vec/ for a contact sheet
    (--sheet --vector)."""
    with lock("vector"):
        return _vectors(force)


def _vectors(force=False):
    import shutil

    import fitz
    from PIL import Image
    from playwright.sync_api import sync_playwright
    labels = list(his.LABELS)
    lost = [lab for lab in labels if not os.path.isfile(os.path.join(DECK, f"{his.stem(lab)}.png"))]
    if lost:
        print(f"vector: no photograph yet for slides {' '.join(lost)}: render them first; nothing written")
        return 1
    rows = manifest()
    if [r["label"] for r in rows] != labels:
        rows = rebuild_manifest()
    titles = [r["title"] for r in rows]
    vec = os.path.join(BUILD, "vec")
    for d in (vec, os.path.join(BUILD, "slides"), os.path.join(BUILD, "review")):
        os.makedirs(d, exist_ok=True)
    write_file(os.path.join(BUILD, "slides", "deck.html"),
               vector.deck_html([(his.stem(lab), slide_body(lab)) for lab in labels]))
    write_file(os.path.join(vec, "view.html"), VIEW)
    printed, tidied = os.path.join(BUILD, "deck-print.pdf"), os.path.join(BUILD, PDF_NAME)
    base = server()
    probs, worst, errors = [], {}, []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--disable-lcd-text", "--font-render-hinting=none"])
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(f"{base}/build/r10-deck/slides/deck.html")
        pg.wait_for_function("window.DECK_READY === true", timeout=120000)
        vector.print_pdf(pg, printed)
        pg.close()
        probs += [f"the deck's page: {e}" for e in errors]
        vector.tidy(printed, tidied, titles, DECK_TITLE, AUTHOR, labels=labels)
        doc = fitz.open(tidied)
        if len(doc) != COUNT:
            probs.append(f"the PDF has {len(doc)} pages, not {COUNT}: a slide ran over its page")
        view = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        for lab, page in zip(labels, doc):
            stem = his.stem(lab)
            with Image.open(os.path.join(DECK, f"{stem}.png")) as im:
                photo = im.convert("RGB")
            z = 1920 / page.rect.width
            pix = page.get_pixmap(matrix=fitz.Matrix(z, z), alpha=False)
            w_pdf = _worst(photo, Image.frombytes("RGB", (pix.width, pix.height), pix.samples), radius=10)
            write_file(os.path.join(vec, f"{stem}.svg"), vector.page_svg(page))
            view.goto(f"{base}/build/r10-deck/vec/view.html?{stem}.svg")
            view.wait_for_function("document.images[0].complete && document.images[0].naturalWidth > 0")
            with Image.open(io.BytesIO(view.screenshot())) as im:
                drawn = im.convert("RGB").resize((1920, 1080), Image.LANCZOS)
            drawn.resize((960, 540), Image.LANCZOS).save(os.path.join(vec, f"{stem}-960.png"))
            w_svg = _worst(photo, drawn, radius=10)
            worst[lab] = {"pdf": w_pdf, "svg": w_svg}
            for kind, w in (("PDF page", w_pdf), ("SVG", w_svg)):
                if w > VEC_TOL:
                    probs.append(f"{stem}: the {kind} differs from the photograph ({w} > {VEC_TOL})")
        doc.close()
        b.close()
    size = os.path.getsize(tidied)
    svgs = [os.path.getsize(os.path.join(vec, f"{his.stem(lab)}.svg")) for lab in labels]
    if size > FILE_MAX:
        probs.append(f"the PDF is {size / 1e6:.2f} MB, over the site's {FILE_MAX / 1e6:.0f} MB a file")
    probs += [f"{his.stem(lab)}: the SVG is {s / 1e6:.2f} MB" for lab, s in zip(labels, svgs) if s > FILE_MAX]
    print(f"vector: {PDF_NAME} {size / 1e6:.2f} MB; {COUNT} SVG {sum(svgs) / 1e6:.2f} MB "
          f"(largest {max(svgs) / 1e3:.0f} KB); against the photographs, worst page "
          f"{max(v['pdf'] for v in worst.values())}, worst SVG {max(v['svg'] for v in worst.values())} "
          f"(limit {VEC_TOL})")
    with open(os.path.join(BUILD, "review", "vector.json"), "w", encoding="utf-8") as fh:
        json.dump({"pdf_bytes": size, "svg_bytes": dict(zip(labels, svgs)), "worst": worst,
                   "problems": probs}, fh, indent=1)
    for pr in probs:
        print("      -", pr)
    if probs and not force:
        print("vector: nothing written")
        return 1
    with open(tidied, "rb") as fh:
        write_file(os.path.join(DECK, PDF_NAME), fh.read())
    for lab in labels:
        stem = his.stem(lab)
        tmp = os.path.join(DECK, "web", f"{stem}.svg.{os.getpid()}.tmp")
        shutil.copyfile(os.path.join(vec, f"{stem}.svg"), tmp)
        _replace(tmp, os.path.join(DECK, "web", f"{stem}.svg"))
    print(f"vector: written, content/deck-probstat/{PDF_NAME} and web/<stem>.svg for {COUNT} slides")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slides", nargs="*", help="labels or ranges: 4, 7a, 1-8, 60-66, all")
    ap.add_argument("--look", action="store_true", help="render and check only; content/ is untouched")
    ap.add_argument("--force", action="store_true", help="write even when a check fails")
    ap.add_argument("--sheet", action="store_true", help="contact sheets of the deck as it stands")
    ap.add_argument("--kit", action="store_true", help="render the component sampler, kit.html")
    ap.add_argument("--vector", action="store_true",
                    help="print the deck's PDF and SVGs (after writing the slides named, if any; "
                         "with --sheet, contact sheets of the SVGs as drawn too)")
    ap.add_argument("--manifest", action="store_true", help="write deck.json again from content/")
    ap.add_argument("--no-anim", action="store_true", help="leave the animation pages alone")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if a.manifest:
        rebuild_manifest()
    if a.sheet or a.kit or (a.vector and not a.slides) or (a.manifest and not a.slides):
        code = vectors(a.force) if a.vector and not a.slides else 0
        if a.sheet:
            sheet()
            if a.vector:
                sheet(drawn=True)
        if a.kit:
            kit()
        if not a.slides:
            return code
    named = slides(a.slides)
    todo = [lab for lab in named if os.path.isfile(src(lab, ".html"))]
    missing = [lab for lab in named if lab not in todo]
    if missing:
        print("no source yet for:", " ".join(missing))
    if not os.path.isdir(ORIG):
        raise SystemExit("content/deck-probstat/_orig/ is missing: back his slides up first")
    os.makedirs(os.path.join(BUILD, "slides"), exist_ok=True)
    for lab in todo:
        stem = his.stem(lab)
        mod = module(lab)
        body = slide_body(lab, mod=mod)
        write_file(os.path.join(BUILD, "slides", f"{stem}.html"), SHELL.format(n=lab, body=body))
        page = anim_page(lab, body, mod) if not a.no_anim else None
        look = os.path.join(ANIM_LOOK, f"{stem}.html")
        if page:
            anim_assets(ANIM_LOOK)
            write_file(look, page)
        elif os.path.isfile(look) and not a.no_anim:
            os.remove(look)
    report, room, rows, anims = shoot(todo, look_only=a.look, force=a.force, with_anim=not a.no_anim)
    bad = 0
    for lab in todo:
        stem = his.stem(lab)
        probs = report[lab]
        state = "ok" if not probs else "FAIL"
        wrote = "" if a.look or (probs and not a.force) else "  written"
        r = room.get(lab)
        space = f"   body {r['top']} to {r['limit']} px, used to {r['used']}" if r else ""
        print(f"{stem}  {state}{wrote}{space}   review: build/r10-deck/review/{stem}.png")
        if lab in anims:
            ai = anims[lab]
            played = ai.get("played") or {}
            print(f"        animation {ai.get('length')} s, {ai.get('actors')} actors, last frame "
                  f"{ai.get('last_frame')} (limit {ANIM_TOL}), slowest frame "
                  f"{played.get('slowest', '?')} ms; frames: build/r10-deck/review/{stem}-anim.png")
        for pr in probs:
            print("      -", pr)
        bad += bool(probs)
    for lab in todo:          # one report per slide: several agents render side by side
        with open(os.path.join(BUILD, "review", f"{his.stem(lab)}.json"), "w", encoding="utf-8") as fh:
            json.dump({"slide": lab, "problems": report[lab], "room": room.get(lab),
                       "animation": anims.get(lab)}, fh, ensure_ascii=False, indent=1)
    if rows:
        update_manifest(rows)
    # The PDF and the SVGs are the whole deck's: printed only when asked
    # (--vector), by the controller once every agent is done, so a print
    # never meets a slide half-way through another agent's work.
    if not a.look and (a.force or len(todo) > bad):
        if a.vector:
            bad += vectors(a.force)
        else:
            print("vector: not printed (the deck's PDF and SVGs: render.py --vector, once, at the end)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
