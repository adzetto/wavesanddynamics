"""Slide 54: his pavement chain of slide 53 run for ten years.

P = [[0.8, 0.2, 0], [0, 0.7, 0.3], [0, 0, 1]] (rows: from; columns: to).
Starting Good, pi_0 = [1, 0, 0] and pi_(t+1) = pi_t P, so pi_t = pi_0 P^t:
pi_1 = [0.80, 0.20, 0], pi_2 = [0.64, 0.30, 0.06] (the tree of slide 53),
pi_10 = [0.107, 0.158, 0.734], his [0.11, 0.16, 0.73]. Failed is absorbing.

shares  the three shares stacked, year by year (straight between the yearly
        values, as he drew them); his labels read the slices at year 2 and
        year 10."""
import numpy as np

from fig import Fig, C, draw, fade, pop, wipe
from s053 import P, tw

# The matrix, the start, then the shares year by year (DECK_BRIEF.md
# "Animated slides"; the blocks' moments are in s054.html): the three bands
# are uncovered as the years pass, the slice at year 2 is read with pi_2 and
# the one at year 10 with pi_10.
ANIM = {"length": 7.5}

T = np.arange(0, 11)
PI = np.array([np.linalg.matrix_power(P, t)[0] for t in T])     # pi_0 = [1, 0, 0]
assert np.allclose(PI[1], [0.80, 0.20, 0])
assert np.allclose(PI[2], [0.64, 0.30, 0.06])
assert np.allclose(np.round(PI[10], 2), [0.11, 0.16, 0.73])
assert np.allclose(PI.sum(axis=1), 1)


def shares():
    f = Fig(976, 622)
    ax = f.axes(118, 12, 838, 492, xlim=(0, 10), ylim=(0, 1), xticks=T,
                yticks=[0, 0.2, 0.4, 0.6, 0.8, 1], ticks="out",
                xlabel="Years (inspection intervals)", ylabel="Share of sections in each state",
                anim=fade(1.2, .4))
    good, worn = PI[:, 0], PI[:, 0] + PI[:, 1]
    ax.area(T, good, 0, color=C.navy, anim=wipe(3.0, 2.0))
    ax.area(T, worn, good, color=C.amber, anim=wipe(3.0, 2.0))
    ax.area(T, 1, worn, color=C.deep, anim=wipe(3.0, 2.0))
    ax.vline(2, color=C.paper, width=2.5, dash="10 7", anim=draw(3.8, .4))
    f.rect(ax.x, ax.y, ax.w, ax.h, stroke=C.ink, width=2, anim=fade(1.2, .4))   # the box over the fills

    def band(x, lo, hi):
        """The middle of a band at year x (straight between the years)."""
        return (np.interp(x, T, lo) + np.interp(x, T, hi)) / 2

    ink = {0: C.paper, 1: C.ink, 2: C.paper}                    # legible on each fill
    bounds = ((np.zeros(11), good), (good, worn), (worn, np.ones(11)))
    # the slice at year 2: 64 / 30 / 6 %, read just right of the line
    for k, (lo, hi) in enumerate(bounds):
        s = f"{round(100 * PI[2, k])}%"
        y = band(2.45, lo, hi) if k < 2 else 0.968
        ax.text(2.1, y, s, "west", size=28, color=ink[k], weight=700, anim=pop(4.0))
    # the slice at year 10: 11 / 16 / 73 %
    for k, (lo, hi) in enumerate(bounds):
        s = f"{round(100 * PI[10, k])}%"
        y = band(9.45, lo, hi) if k < 2 else 0.5
        ax.text(9.84, y, s, "east", size=28, color=ink[k], weight=700, anim=pop(5.3))
    ax.legend([("Good", {"kind": "area", "color": C.navy}),
               ("Degraded", {"kind": "area", "color": C.amber}),
               ("Failed", {"kind": "area", "color": C.deep})], at="north east", size=26, row=38,
              anim=pop(3.0))
    assert tw("Degraded", 26) < 26 * 0.5 * 8 + 6          # the legend's box holds its words
    return f.html()
