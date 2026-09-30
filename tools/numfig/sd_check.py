"""The overlap record the shmdocs figures append to their check files.

common.still() already refuses a figure whose type collides at its poster
or at any quarter second up to its poster time. With --dense a generator
also sweeps every `step` seconds over two whole loops (the first loop and
the second can differ: a spectrum that builds up once, a panel's idle
state before its next cycle), and writes what it found.
"""
import numpy as np

import common


def record(name, loop_end, step=0.1, dense=False, knock=None):
    """Lines for the check file: the still's own check, and with `dense` the
    sweep's result. Raises if the sweep finds a collision. `knock` names a
    label that sits on a white knockout drawn after the line under it."""
    lines = ["", "OVERLAP (engine.js ?overlap)",
             "  common.still(): at the poster and every 0.25 s up to the poster time: no label meets a label,",
             "  no stroke crosses a label (the still would not have been written otherwise)"]
    if dense:
        times = [round(float(x), 2) for x in np.arange(step, loop_end + 1e-9, step)]
        res = common.overlaps(name, times)
        bad = {k: v for k, v in res.items() if v["labels"] or v["crossings"]}
        lines.append(f"  common.overlaps() every {step:g} s from {times[0]:g} to {times[-1]:g} s (two loops,"
                     f" {len(res)} moments): " + ("nothing collides" if not bad else f"{len(bad)} moments collide"))
        if bad:
            raise RuntimeError(f"nf-{name}: collisions at " + ", ".join(list(bad)[:10]))
    if knock:
        lines.append(f"  one label sits on a knockout by design: {knock}; nothing is allowed (still(allow=()))")
    else:
        lines.append("  no knockout is relied on and nothing is allowed (still(allow=()))")
    return lines


def append(path, lines):
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def poster_js(js, poster):
    """The script with its printed moment written as a number: common.still()
    reads POSTER_T from the page to know how far its overlap check must run."""
    old = "const POSTER_T = D.poster;"
    assert js.count(old) == 1, "the script names POSTER_T once, from DATA"
    return js.replace(old, f"const POSTER_T = {float(poster):g};")
