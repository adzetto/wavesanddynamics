"""What the sound document's three figures share: the overlap check over a
whole loop of their motion (common.still() checks up to the poster only)."""
import common


def loop_overlaps(name, end, step=0.1):
    """Run engine.js's overlap check at the poster and every `step` seconds
    from `step` to `end` (a whole loop and more); raise on any label that
    meets another or any stroke through a label. Returns the lines for the
    figure's .check.txt."""
    times = [round(step * k, 3) for k in range(1, int(round(end / step)) + 1)]
    r = common.overlaps(name, times)
    faults = [f"{when}: {v}" for when, v in r.items() if v["labels"] or v["crossings"]]
    if faults:
        raise RuntimeError(f"nf-{name}: ink collides:\n  " + "\n  ".join(faults[:20]))
    return ["OVERLAP (engine.js ?overlap, through common.overlaps)",
            f"  the poster and every {step:g} s from {step:g} to {times[-1]:g} s ({len(r)} moments, the intro",
            "  and a whole loop of the motion): no label meets another, no stroke crosses a label;",
            "  nothing is excused (common.still is called with no allow list)."]


def append(path, lines):
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n" + "\n".join(lines) + "\n")
