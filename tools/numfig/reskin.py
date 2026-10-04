r"""reskin.py -- rebuild figure pages with the current frame, engine and
figure scripts, keeping each page's own numbers (README.md, "Restyling a
figure").

    python tools/numfig/reskin.py NAME [NAME ...] [--still] [--dry-run]
    python tools/numfig/reskin.py --all [--dry-run]       # every nf-*.html page
    python tools/numfig/reskin.py --all-ml [--still]      # nf-ml-*, nf-mla-*, nf-mlb-*, nf-mlc-*

NAME is the page's name without nf- (mlb-uat for nf-mlb-uat.html).

A page (common.build_html) is the frame HEAD filled in with the figure's
title, aria text, size and DATA, then engine.js, then the figure's script.
A restyle (its buttons, its colours, its type) changes the frame, the engine
or the script, and nothing of DATA. Running the generator again would train
its model again: slow, impossible where torch or statsmodels is missing, and
with another library version perhaps other numbers. reskin rebuilds the page
from what it holds:

- the frame: the current common.HEAD, filled in with the title, aria text,
  size and DATA the page holds, verbatim;
- the engine: the current engine.js, in place of whatever version the page
  was built with (it ends where the engine's last function, b64i8, ends);
- the script: the page's own, with every change made since the last commit
  to the scripts of the figure's generator and of the library it writes
  through (the JS strings of <module>.py; mla_shared.LIB, mlb_common.JS_LIB,
  mlc_lib.LIB). Each change is found in the page by its lines and two lines
  around it, and must be found exactly once;
- the title and aria text: the page's own, or the generator's where it changed
  them since the last commit (TITLE and ARIA, or the strings it hands
  build_html, mlb_common.publish or mlc_lib.build).

The page it starts from is the page as last committed, since the changes are
counted from there too: reskin can be run again after more edits.

Nothing is imported or run to do this. --verify (on by default) then checks
the script against the generator itself where it can be imported (a copy of
the sources in a temp folder, torch and statsmodels stood in for), and
refuses a page whose script the committed generator would not write.

--still photographs the new page's poster into nf-<name>.webp as
common.still() does, and fails on any fault of the overlap check that the
old page did not have.
"""
import argparse
import ast
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import common  # noqa: E402

TAIL = "\n</script>\n</body>\n</html>\n"
ENGINE_END = "\nfunction b64i8(s) {"          # the engine's last function
LIBS = (("mla_shared", "LIB"), ("mlb_common", "JS_LIB"), ("mlc_lib", "LIB"))
PLACE = "\x00"                                # an f-string's {value}: never matched


# ------------------------------------------------------------------ a page
def split(page):
    """A page as (what it holds for the frame, its engine, its script)."""
    held = {"title": re.search(r"<title>(.*?)</title>", page, re.S).group(1),
            "aria": re.search(r'<canvas id="c" role="img" aria-label="(.*?)"></canvas>', page, re.S).group(1)}
    held["w"], held["h"] = re.search(r"\nconst W = (\d+), H = (\d+);\n", page).groups()
    start = page.index("\nconst DATA = ") + len("\nconst DATA = ")
    end = page.index("\n", start)
    if page[end - 1] != ";" or not page.endswith(TAIL):
        raise ValueError("not a page build_html wrote")
    held["data"] = page[start:end - 1]
    at = page.index(ENGINE_END, end)
    stop = page.index("\n", at + 1) + 1
    if page[stop] != "\n":
        raise ValueError("no blank line between the engine and the script")
    return held, page[end + 1:stop], page[stop + 1:-len(TAIL)]


# ------------------------------------------------------------------ scripts
def literals(source, names):
    """The strings a module assigns at its top level to any of `names`, each
    as its lines, in order; an f-string's values are PLACE."""
    out = []
    for node in ast.parse(source).body if source else ():
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets):
            inner = {id(v) for j in ast.walk(node.value) if isinstance(j, ast.JoinedStr) for v in j.values}
            for sub in ast.walk(node.value):
                if isinstance(sub, ast.JoinedStr):
                    out.append("".join(v.value if isinstance(v, ast.Constant) else PLACE for v in sub.values))
                elif isinstance(sub, ast.Constant) and isinstance(sub.value, str) and id(sub) not in inner:
                    out.append(sub.value)
    return [t.split("\n") for t in out]


def committed(path):
    """A file of the repository as last committed ('' if it was not)."""
    r = subprocess.run(["git", "-C", ROOT, "show", f"HEAD:{os.path.relpath(path, ROOT)}"],
                       capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else ""


def changes(old, new, where):
    """Each change from the strings `old` to `new` (lists of lines), with
    two lines around it, as (old passage, new passage)."""
    if len(old) != len(new):
        raise SystemExit(f"{where}: its scripts were rearranged, not edited; run the generator itself")
    out = []
    for o, n in zip(old, new):
        for group in difflib.SequenceMatcher(None, o, n, autojunk=False).get_grouped_opcodes(2):
            out.append((o, n, group))
    return out


def patch(script, edits, where):
    """The script with each change made, each found by its passage widened
    until it is found exactly once."""
    def passage(lines, lo, hi):
        # build_html strips the whole script: a string's first and last lines
        # may have lost their blank space in the page
        t = "\n".join(lines[max(0, lo):hi])
        t = t.lstrip() if lo <= 0 else t
        return t.rstrip() if hi >= len(lines) else t

    for o, n, group in edits:
        (_, i1, _, j1, _), (_, _, i2, _, j2) = group[0], group[-1]
        for wider in (0, 2, 6, 14, 30):
            a = passage(o, i1 - wider, i2 + wider)
            if script.count(a) == 1 or i1 - wider <= 0 and i2 + wider >= len(o):
                break
        b = passage(n, j1 - wider, j2 + wider)
        if PLACE in a or PLACE in b:
            raise SystemExit(f"{where}: a change touches an f-string's value; run the generator itself")
        if script.count(a) != 1:
            raise SystemExit(f"{where}: a changed passage is found {script.count(a)} times in the page, "
                             f"not once:\n{a[:400]}")
        script = script.replace(a, b)
    return script


def module_of(name):
    return name.replace("-", "_")


def edits_for(name, script):
    """The changes since the last commit to the scripts that write this page:
    its generator's, and its library's if the page holds that library's."""
    out = []
    mod = os.path.join(HERE, module_of(name) + ".py")
    if os.path.isfile(mod):          # a page some other module writes keeps its script
        with open(mod, encoding="utf-8") as fh:
            out += changes(literals(committed(mod), {"JS"}), literals(fh.read(), {"JS"}), f"nf-{name}")
    for lib, var in LIBS:
        path = os.path.join(HERE, lib + ".py")
        old = literals(committed(path), {var})
        with open(path, encoding="utf-8") as fh:
            new = literals(fh.read(), {var})
        if old != new and old and "\n".join(old[0][:12]).strip() in script:
            out += changes(old, new, f"{lib}.{var}")
    return out


def _label(source, var, argi):
    """A module's title or aria text: the string it assigns to `var` at its top
    level, or else the one it hands its page builder (build_html, publish,
    build) as argument `argi`; None if neither is a plain string."""
    if not source:
        return None
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == var for t in node.targets):
            v = node.value
            return v.value if isinstance(v, ast.Constant) and isinstance(v.value, str) else None
    found = [n.args[argi].value for n in ast.walk(tree)
             if isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", "")) in
             ("build_html", "publish", "build") and len(n.args) > argi
             and isinstance(n.args[argi], ast.Constant) and isinstance(n.args[argi].value, str)]
    return found[0] if len(found) == 1 else None


def labels_for(name, held):
    """What the page holds for the frame, with a change made since the last
    commit to its generator's title or aria text carried over (build_html
    writes the aria text with its quotes as &quot;)."""
    mod = os.path.join(HERE, module_of(name) + ".py")
    out = dict(held)
    if not os.path.isfile(mod):
        return out
    with open(mod, encoding="utf-8") as fh:
        new_src = fh.read()
    old_src = committed(mod)
    for key, var, argi, esc in (("title", "TITLE", 1, lambda t: t), ("aria", "ARIA", 2, lambda t: t.replace('"', "&quot;"))):
        o, n = _label(old_src, var, argi), _label(new_src, var, argi)
        if o is not None and n is not None and o != n:
            if held[key] != esc(o):
                raise SystemExit(f"nf-{name}: its {key} is not the committed generator's; run the generator itself")
            out[key] = esc(n)
    return out


# ------------------------------------------------------------------ verify
PROBE = r'''
import importlib.abc, importlib.machinery, importlib.util, json, sys, types
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])


class Stand(type):
    """What a missing library's name gives at import time: a class (other
    libraries' issubclass() checks of torch.Tensor work) whose attributes and
    calls give it back."""
    def __getattr__(cls, k):
        if k.startswith("__") and k.endswith("__"):
            raise AttributeError(k)
        return Any
    def __call__(cls, *a, **k): return cls


class Any(metaclass=Stand):
    pass


class Missing(types.ModuleType):
    __path__ = []
    def __getattr__(self, k):
        if k.startswith("__") and k.endswith("__"):
            raise AttributeError(k)
        return Any


class StandIn(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, roots): self.roots = roots
    def find_spec(self, name, path, target=None):
        if name.split(".")[0] in self.roots:
            return importlib.machinery.ModuleSpec(name, self, is_package=True)
    def create_module(self, spec): return Missing(spec.name)
    def exec_module(self, module): pass


sys.meta_path.insert(0, StandIn({m for m in ("torch", "statsmodels") if importlib.util.find_spec(m) is None}))
js = importlib.import_module(sys.argv[2]).JS
if "mlb_common" in sys.modules:
    js = sys.modules["mlb_common"].JS_LIB + js
elif "mlc_lib" in sys.modules:
    js = sys.modules["mlc_lib"].LIB + "\n" + js
print("\n@@PROBE@@" + json.dumps(js.strip()))
'''


def tree(kind):
    """tools/numfig, as committed ('old') or as it is now ('new'), copied into
    a temp folder: a generator may write files when it is imported."""
    tmp = tempfile.mkdtemp(prefix=f"reskin-{kind}-")
    os.makedirs(os.path.join(tmp, "content", "anim"))
    dst = os.path.join(tmp, "tools", "numfig")
    if kind == "old":
        tar = os.path.join(tmp, "numfig.tar")
        subprocess.run(["git", "-C", ROOT, "archive", "-o", tar, "HEAD", "tools/numfig"], check=True)
        with tarfile.open(tar) as t:
            t.extractall(tmp, filter="data")
    else:
        shutil.copytree(HERE, dst, ignore=shutil.ignore_patterns("__pycache__"))
    return dst


def generated(folder, name):
    """The script the generator in `folder` hands build_html, or None where it
    cannot be imported here (or no module has the page's name)."""
    if not os.path.isfile(os.path.join(folder, module_of(name) + ".py")):
        return None
    r = subprocess.run([sys.executable, "-c", PROBE, folder, module_of(name)], capture_output=True,
                       text=True, encoding="utf-8", cwd=folder)
    if r.returncode or "@@PROBE@@" not in r.stdout:
        return None
    return json.loads(r.stdout.rsplit("@@PROBE@@", 1)[1])


# ------------------------------------------------------------------ a page, again
def photograph(name, width=672, quality=92):
    """common.still() without its raise: the poster as nf-<name>.webp."""
    from PIL import Image
    look = os.path.join(tempfile.gettempdir(), f"nf-{name}-still.png")
    common._shoot(name, [("still", look)], width)
    with Image.open(look) as im:
        im.convert("RGB").save(os.path.join(common.ANIM, f"nf-{name}.webp"), "WEBP",
                               quality=quality, method=6)
    return look


def reskin(name, trees, still=False, dry=False, verify=True):
    path = os.path.join(common.ANIM, f"nf-{name}.html")
    with open(path, encoding="utf-8") as fh:
        page = fh.read()
    # the changes are counted from the last commit, so they are made in the page
    # as committed: after more edits, reskin makes all of them once
    held, engine, script = split(committed(path) or page)
    fresh_script = patch(script, edits_for(name, script), f"nf-{name}")
    if verify:
        old = generated(trees["old"], name)
        if old is not None and old != script:
            print(f"nf-{name}: REFUSED, the committed generator writes another script; run the generator itself")
            return False
        new = generated(trees["new"], name) if old is not None else None
        if new is not None and new != fresh_script:
            print(f"nf-{name}: REFUSED, the patched script is not the one the generator writes")
            return False
        how = "checked against its generator" if new is not None else "generator not importable here"
    else:
        how = "not checked"
    labels = labels_for(name, held)
    with open(os.path.join(HERE, "engine.js"), encoding="utf-8") as fh:
        fresh = common.HEAD.format(**labels) + fh.read() + "\n" + fresh_script + TAIL
    for d in common.DASHES:
        if d in fresh:
            raise SystemExit(f"nf-{name}: a dash the site does not use ({d!r})")
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", fresh):
        raise SystemExit(f"nf-{name}: something that reads as an email address")
    if fresh == page:
        print(f"nf-{name}: unchanged")
        return True
    new_held, new_engine, _ = split(fresh)
    disk_held, disk_engine, disk_script = split(page)
    what = [k for k, gone in (("frame", fresh[:fresh.index("\nconst W = ")] != page[:page.index("\nconst W = ")]),
                              ("engine", new_engine != disk_engine), ("script", fresh_script != disk_script)) if gone]
    what += [k for k in ("title", "aria") if labels[k] != disk_held[k]]
    assert new_held == labels and {k: held[k] for k in ("w", "h", "data")} == {k: labels[k] for k in ("w", "h", "data")}
    print(f"nf-{name}: new {', '.join(what)}; DATA kept; {how}")
    if dry:
        return True
    before = set(common.collisions(name)) if still else set()
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(fresh)
    if still:
        print(f"  still {photograph(name)}")
        added = sorted(set(common.collisions(name)) - before)
        if added:
            print(f"  nf-{name}: new collisions:\n    " + "\n    ".join(added[:20]))
            return False
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("names", nargs="*")
    ap.add_argument("--all", action="store_true", help="every nf-*.html page")
    ap.add_argument("--all-ml", action="store_true", help="every nf-ml-*, nf-mla-*, nf-mlb-*, nf-mlc-* page")
    ap.add_argument("--still", action="store_true", help="photograph the poster and run the overlap check")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-verify", action="store_true", help="do not import the generators to check")
    a = ap.parse_args()
    names = list(a.names)
    pages = sorted(f[3:-5] for f in os.listdir(common.ANIM) if f.startswith("nf-") and f.endswith(".html"))
    if a.all:
        names += pages
    elif a.all_ml:
        names += [n for n in pages if re.fullmatch(r"ml[abc]?-.+", n)]
    if not names:
        ap.error("name a page, or --all, or --all-ml")
    trees = {} if a.no_verify else {"old": tree("old"), "new": tree("new")}
    ok = [reskin(n, trees, a.still, a.dry_run, not a.no_verify) for n in names]
    sys.exit(0 if all(ok) else 1)


if __name__ == "__main__":
    main()
