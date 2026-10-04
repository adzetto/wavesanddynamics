r"""make.py -- build the blog's figures in house style v3 (README.md).

    python tools/blogfig/make.py [name ...] [--no-check] [--dpi 300]

Every figure is a module of this folder, <name>.py, with SLUG and STEM (the
post and the picture it redraws: content/blog/<slug>/text/<stem>.png, which
post_page() in site/build.py publishes as post/<slug>/<k>-<stem>.*) and
body(), the TikZ picture as a string: Python computes the geometry and reads
the data, TeX only gives the style. A figure that places its labels by
their boxes asks geom.size(); the first time it is asked for a label TeX has
not measured, make.py measures them all and asks for the picture again.
make.py writes the wrapper (10 pt Computer Modern, a 4 pt margin, figstyle.tex), runs
pdflatex, the checks of fscheck.py (label clearance >= 1.5 pt, label pairs
>= 1.5 pt, no bare arrow tips, width <= 165 mm) and pdftocairo:
content/blog-figs/<slug>/<stem>.svg, glyphs outlined, its numbers to
0.01 pt, on white paper (slim()), which build.py publishes in the picture's place, and
build/blogfig/<name>.png to look at. Exit code 1 if a figure does not compile
or fails a check: a figure that fails is not written.
"""
import importlib
import os
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BUILD = os.path.join(ROOT, "build", "blogfig")
OUT = os.path.join(ROOT, "content", "blog-figs")
sys.path.insert(0, HERE)
FIGS = ["som_fig1", "som_fig2", "som_fig3", "ldv_speckle", "moo_fig1", "moo_fig2", "moo_fig3", "swpt_fig1"]
WRAP = r"""\documentclass[10pt,tikz,border=4pt]{{standalone}}
\input{{figstyle}}
\begin{{document}}
{body}
\end{{document}}
"""


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="ignore")


def slim(path):
    """The SVG as pdftocairo wrote it, its numbers to 0.01 pt (a hundredth of a
    point is a thirtieth of a pixel on the page) and no space between its tags,
    on white paper: the site draws a figure's white into the page in its light
    scheme (mix-blend-mode: multiply) and shows it as a white card in its dark
    one, where a transparent figure's black lines would vanish."""
    def r(m):
        t = f"{float(m.group(0)):.2f}".rstrip("0").rstrip(".")
        return "0" if t in ("-0", "") else t
    with open(path, encoding="utf-8") as f:
        s = f.read()
    s = re.sub(r"-?\d+\.\d{3,}", r, s)
    s = re.sub(r">\s+<", "><", s)
    vb = re.search(r'<svg\b[^>]*\sviewBox="0 0 ([\d.]+) ([\d.]+)"[^>]*>', s)
    paper = f'<rect width="{vb.group(1)}" height="{vb.group(2)}" fill="#fff"/>'
    at = s.find("</defs>")
    at = at + len("</defs>") if at >= 0 else vb.end()
    s = s[:at] + paper + s[at:]
    # opened on its own (a post links a wide figure to its file) it fills the window, its
    # proportions kept by the viewBox; in a page the <img> gives its size (build.redrawn)
    s = re.sub(r'(<svg\b[^>]*?)\swidth="[\d.]+(?:pt)?"\s+height="[\d.]+(?:pt)?"',
               r'\1 width="100%" height="100%"', s, count=1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def build(name, dpi, check):
    mod = importlib.import_module(name)
    os.makedirs(BUILD, exist_ok=True)
    shutil.copy(os.path.join(HERE, "figstyle.tex"), BUILD)
    for extra in getattr(mod, "FILES", ()):        # pictures a figure draws over (a dense cloud of points)
        shutil.copy(os.path.join(BUILD, extra) if os.path.isfile(os.path.join(BUILD, extra))
                    else os.path.join(HERE, extra), BUILD)
    tex = name + ".tex"
    import geom
    try:
        body = mod.body()
    except AssertionError:           # a check on guessed label sizes: measure them first
        if not geom.MISSING:
            raise
        body = None
    if geom.measure() or body is None:   # labels TeX had not measured yet: place them again
        body = mod.body()
    with open(os.path.join(BUILD, tex), "w", encoding="utf-8", newline="\n") as f:
        f.write(WRAP.format(body=body))
    run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex], BUILD)
    log = open(os.path.join(BUILD, name + ".log"), errors="ignore").read()
    err = re.findall(r"^!.*$", log, re.M)
    if err or not os.path.isfile(os.path.join(BUILD, name + ".pdf")):
        print(f"  {name}: ERROR {err[:3]}")
        return False
    ok = True
    if check:
        import fscheck
        ok = fscheck.check(os.path.join(BUILD, name + ".pdf"), quiet=True, verbose=True)
    run(["pdftocairo", "-png", "-r", str(dpi), "-singlefile", name + ".pdf", name], BUILD)
    if ok:
        dst = os.path.join(OUT, mod.SLUG)
        os.makedirs(dst, exist_ok=True)
        svg = os.path.join(dst, mod.STEM + ".svg")
        run(["pdftocairo", "-svg", name + ".pdf", svg], BUILD)
        slim(svg)
    print(f"  {name} -> {'content/blog-figs/' + mod.SLUG + '/' + mod.STEM + '.svg' if ok else 'not written'},"
          f" build/blogfig/{name}.png{'' if ok else '   CHECK FAILED'}")
    return ok


def main(argv):
    dpi = 300
    if "--dpi" in argv:
        i = argv.index("--dpi")
        dpi = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    check = "--no-check" not in argv
    names = [a for a in argv if not a.startswith("--")] or FIGS
    ok = True
    for n in names:
        ok &= build(n, dpi, check)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
