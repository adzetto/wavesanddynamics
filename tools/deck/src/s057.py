"""Slide 57: his Gaussian-process prior for cone resistance qc along a 10 m
site, before any tests (his notes; illustrative, not calibrated).

Mean m(x) = 6 MPa everywhere, standard deviation sigma = 1 MPa, squared-
exponential kernel k(x, x') = sigma^2 exp[-(x - x')^2 / (2 l^2)], with
l = 0.6 m (rough) and l = 2.5 m (smooth). The band is the prior's +-2 SD,
4 to 8 MPa. Each panel draws four realizations on a 0.025 m grid: f = m +
V sqrt(W) z, with K = V W V^T (eigh; K is too smooth for Cholesky) and z
standard normal from numpy's PCG64 generator with a fixed seed, so the same
curves come back on every run. The legend runs in one row (legend_row, a
helper the shared fig.py does not have) so that it clears the curves."""
import numpy as np

from fig import Fig, C, SERIES, draw, fade, pop
from s053 import tw

# The rough prior, then the smooth one (DECK_BRIEF.md "Animated slides"; the
# blocks' moments are in s057.html): each panel's mean and band, then its
# four possible profiles drawn one after another.
ANIM = {"length": 8.1}

MEAN, SD = 6.0, 1.0
X = np.linspace(0, 10, 401)
SEED = 57
COLORS = SERIES[:4]                          # navy, accent, blue, sky
STYLE = (None, None, "12 6", None)           # navy and blue differ by line style too


def kernel(a, b, ell, sd=SD):
    return sd ** 2 * np.exp(-(a[:, None] - b[None, :]) ** 2 / (2 * ell ** 2))


def draws(ell, z):
    w, v = np.linalg.eigh(kernel(X, X, ell))
    return MEAN + (v * np.sqrt(np.clip(w, 0, None))) @ z


_rng = np.random.default_rng(SEED)
Z = {ell: _rng.standard_normal((len(X), 4)) for ell in (0.6, 2.5)}
CURVES = {ell: draws(ell, z) for ell, z in Z.items()}
assert np.isclose(kernel(np.array([0.0]), np.array([0.0]), 1)[0, 0], SD ** 2)


def legend_row(ax, entries, size=26, pad=12, sample=44, gap=30, inset=14, anim=None):
    """pgfplots' legend with its entries in one row (legend columns=-1): a
    1 px ink box, white, in the axis' top right corner. Returns its box."""
    import re
    f = ax.f
    widths = [tw(re.sub(r"<[^>]+>", "", t), size) for t, _ in entries]
    bw = 2 * pad + sum(sample + 10 + w for w in widths) + gap * (len(entries) - 1)
    bh = 2 * pad + size + 4
    bx, by = ax.x + ax.w - inset - bw, ax.y + inset
    f.rect(bx, by, bw, bh, fill=C.paper, stroke=C.ink, width=1.0, anim=anim)
    x, cy = bx + pad, by + bh / 2
    for (t, st), w in zip(entries, widths):
        if st.get("kind") == "area":
            f.rect(x, cy - 10, sample, 20, fill=st["color"], anim=anim)
        else:
            f.line([(x, cy), (x + sample, cy)], stroke=st["color"], width=st.get("width", 3),
                   dash=st.get("dash"), cap="butt", anim=anim)
        f.text(x + sample + 10, cy, t, "west", size=size, anim=anim)
        x += sample + 10 + w + gap
    return bx, by, bw, bh


def _panel(ell, t0):
    f = Fig(832, 440)
    ax = f.axes(96, 8, 716, 334, xlim=(-0.5, 10.5), ylim=(2.5, 10.1), xticks=range(0, 11, 2),
                yticks=range(3, 10), xlabel="Distance along the site (m)",
                ylabel="Cone resistance qc (MPa)", anim=fade(t0 + .2, .4))
    ax.area([0, 10], MEAN + 2 * SD, MEAN - 2 * SD, color=C.steel, anim=fade(t0 + .6, .4))
    ax.hline(MEAN, color=C.ink, width=2, dash="8 6", anim=draw(t0 + .6, .5))
    ys = CURVES[ell]
    for k in range(4):
        ax.plot(X, ys[:, k], color=COLORS[k], width=3, dash=STYLE[k], anim=draw(t0 + 1.0 + .3 * k, .8))
    bx, by, bw, bh = legend_row(ax, [("±2 SD (95%)", {"kind": "area", "color": C.steel}),
                                     ("prior mean 6 MPa", {"color": C.ink, "dash": "8 6", "width": 2})],
                                anim=pop(t0 + .6))
    # no curve runs under the legend
    inside = (ax.X(X) > bx - 6) & (ax.X(X) < bx + bw + 6)
    assert (ax.Y(ys[inside]) > by + bh + 4).all(), f"a curve meets the legend (l = {ell})"
    return f.html()


def rough():
    return _panel(0.6, 0.3)


def smooth():
    return _panel(2.5, 3.8)
