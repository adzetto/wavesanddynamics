"""Slide 2, the whole workflow: the small pictures in each box, every one
computed from a stated model (numpy, scipy), drawn as TikZ would.

Samples are deterministic Halton draws (fig.sample), so the pictures are the
same on every run. The numbers behind the reliability pictures are his own
worked example (slides 36 to 38): capacity R ~ N(100, 10) kN, demand
S ~ N(70, 8) kN, independent.
"""
import numpy as np
from scipy import stats

from fig import Fig, C, mix, sample

# The map builds in the order data travels (DECK_BRIEF.md "Animated slides";
# the moments are in s002.html): the data, the three optional statistics
# stages and the paths through them, the probability models and risk, then
# the two ways of reading the result for a decision; each arrow draws just
# before the box it leads to. Each small figure arrives with its box.
ANIM = {"length": 10.9}

LAB = 20                 # label size on this slide (the map's small print)
W1, W4, W5 = 228, 340, 350   # figure widths: stages 1 to 3, box 4, box 5


def _base(f, y, x0=0, x1=None):
    f.line([(x0, y), (x1 if x1 is not None else f.w, y)], stroke=C.ink, width=1.6, cap="butt")


def _curve(ax, dist, lo, hi, color=C.navy, width=2.6, dash=None, n=300):
    x = np.linspace(lo, hi, n)
    ax.plot(x, dist.pdf(x), color=color, width=width, dash=dash)
    return x


# ------------------------------------------------------------------ stage 1
def chi():
    """A histogram of 400 draws from a skewed quantity (lognormal) against
    three candidate families fitted to the same draws by maximum likelihood:
    normal, lognormal, exponential."""
    f = Fig(W1, 84)
    pw = 136                                    # the plot; his label beside it
    ax = f.axes(0, 6, pw, 72, xlim=(0, 3.6), ylim=(0, 1.02), frame=False)
    xs = sample(400, stats.lognorm(0.45))
    edges = np.linspace(0, 3.6, 13)
    h, _ = np.histogram(xs, edges, density=True)
    mid = (edges[:-1] + edges[1:]) / 2
    ax.bars(mid, h, width=(edges[1] - edges[0]) * 0.86, color=C.steel2)
    x = np.linspace(0.01, 3.6, 300)
    mu, sd = xs.mean(), xs.std()
    s, loc, sc = stats.lognorm.fit(xs, floc=0)
    ax.plot(x, stats.norm(mu, sd).pdf(x), color=C.accent, width=2.6)
    ax.plot(x, stats.lognorm(s, 0, sc).pdf(x), color=C.navy, width=2.6)
    ax.plot(x, stats.expon(0, mu).pdf(x), color=C.sky, width=2.4, dash="6 4")
    _base(f, 78, 0, pw)
    f.text(pw + 12, 42, "Different <br>probability <br>distributions", "west", size=LAB)
    return f.html()


def qq():
    """A normal probability plot of 12 draws: ordered values against the
    normal quantiles at Blom's plotting positions, and the line they should
    follow."""
    f = Fig(W1, 52)
    n = 12
    z = np.sort(sample(n, stats.norm(), skip=40))
    q = stats.norm.ppf((np.arange(1, n + 1) - 0.375) / (n + 0.25))
    ax = f.axes(16, 4, W1 - 32, 44, xlim=(-2.1, 2.1), ylim=(-2.3, 2.3), frame=False)
    ax.plot([-2.1, 2.1], [-2.1, 2.1], color=C.sky, width=2, dash="7 5")
    ax.scatter(q, z, r=4.6, color=C.accent)
    return f.html()


# ------------------------------------------------------------------ stage 2
def moments():
    """Estimated mean and variance: a histogram of 300 draws and the normal
    density with the sample mean and standard deviation."""
    f = Fig(W1, 88)
    ax = f.axes(8, 24, W1 - 16, 58, xlim=(-3.2, 3.2), ylim=(0, 0.46), frame=False)
    xs = sample(300, stats.norm(), skip=7)
    edges = np.linspace(-3.2, 3.2, 12)
    h, _ = np.histogram(xs, edges, density=True)
    mid = (edges[:-1] + edges[1:]) / 2
    ax.bars(mid, h, width=(edges[1] - edges[0]) * 0.86, color=C.steel2)
    m, s = xs.mean(), xs.std(ddof=1)
    x = np.linspace(-3.2, 3.2, 300)
    ax.plot(x, stats.norm(m, s).pdf(x), color=C.accent, width=2.6)
    X, Y = ax.P(m, stats.norm(m, s).pdf(m))
    f.circle(X, Y, 6, fill=C.accent, stroke=C.paper, width=2)
    f.text(X, Y - 10, "mean", "south", size=LAB)
    y1 = stats.norm(m, s).pdf(m + s)
    x0, yy = ax.P(m, y1)
    x1, _ = ax.P(m + s, y1)
    f.arrow((x0, yy), (x1 + 2, yy), color=C.accent, width=2)
    f.line([(x1 + 3, yy - 8), (x1 + 3, yy + 8)], stroke=C.accent, width=2, cap="butt")
    f.text(x1 + 10, yy - 4, "variance", "south west", size=LAB)
    _base(f, 82)
    return f.html()


def fit_line():
    """Correlation and regression: 10 points with correlation 0.8 and their
    least-squares line."""
    f = Fig(W1, 56)
    x, y = sample(10, stats.norm(), stats.norm(), rho=-0.85, skip=3)
    ax = f.axes(10, 4, W1 - 20, 48, xlim=(-2.2, 2.2), ylim=(-2.4, 2.4), frame=False)
    b, a = np.polyfit(x, y, 1)
    xx = np.array([-2.2, 2.2])
    ax.plot(xx, a + b * xx, color=C.accent, width=2.6)
    ax.scatter(x, y, r=4.4, color=C.navy)
    f.text(W1 - 40, 10, "<m>r</m>", "north", size=LAB + 2)
    return f.html()


# ------------------------------------------------------------------ stage 3
def interval():
    """A 95% confidence interval for a mean (25 draws, known sigma), the
    estimate at its centre, and a hypothesised value H0 outside it."""
    f = Fig(W1, 56)
    xs = sample(25, stats.norm(32, 3), skip=11)
    m = xs.mean()
    half = 1.96 * 3 / 5
    ax = f.axes(10, 4, W1 - 20, 30, xlim=(m - 2.6, m + 2.6), ylim=(0, 1), frame=False)
    y = 0.5
    ax.plot([m - half, m + half], [y, y], color=C.navy, width=2.6)
    for e in (m - half, m + half):
        ax.plot([e, e], [y - .32, y + .32], color=C.navy, width=2.6)
    h0 = m + 1.35 * half
    ax.vline(h0, color=C.ink, width=1.8, dash="6 4", y0=0.0, y1=1.0)
    ax.mark(m, y, r=6.5)
    X, _ = ax.P(h0, 0)
    f.text(X + 8, 30, "<m>H₀</m>", "west", size=LAB)
    return f.html()


def band():
    """Regression inference: a least-squares line through 20 points and the
    95% confidence band of the mean response."""
    f = Fig(W1, 56)
    x, y = sample(20, stats.norm(), stats.norm(), rho=-0.7, skip=21)
    X = np.column_stack([np.ones_like(x), x])
    beta, res, *_ = np.linalg.lstsq(X, y, rcond=None)
    n = len(x)
    s2 = ((y - X @ beta) ** 2).sum() / (n - 2)
    xx = np.linspace(-2.3, 2.3, 120)
    Xg = np.column_stack([np.ones_like(xx), xx])
    se = np.sqrt(s2 * np.einsum("ij,jk,ik->i", Xg, np.linalg.inv(X.T @ X), Xg))
    t = stats.t.ppf(0.975, n - 2)
    yh = Xg @ beta
    ax = f.axes(10, 3, W1 - 20, 50, xlim=(-2.3, 2.3), ylim=(-2.0, 2.0), frame=False)
    ax.area(xx, yh + t * se, yh - t * se, color=C.mist)
    ax.plot(xx, yh, color=C.accent, width=2.6)
    return f.html()


# ------------------------------------------------------------------ box 4
def venn():
    f = Fig(W4, 58)
    cx, cy, r = W4 / 2, 29, 27
    f.circle(cx - 20, cy, r, fill=C.steel2, stroke=C.navy, width=2)
    f.circle(cx + 20, cy, r, fill=C.wash, stroke=C.accent, width=2, opacity=None)
    # the overlap, A and B together
    h = (r * r - 20 * 20) ** 0.5
    f.els.append(f'<path d="M{cx} {cy - h:.2f} A{r} {r} 0 0 1 {cx} {cy + h:.2f} A{r} {r} 0 0 1 {cx} {cy - h:.2f} Z" '
                 f'fill="{mix(C.amber, C.paper, .43)}" stroke="none"/>')
    f.circle(cx - 20, cy, r, fill="none", stroke=C.navy, width=2)
    f.circle(cx + 20, cy, r, fill="none", stroke=C.accent, width=2)
    f.text(cx - 33, cy, "<m>A</m>", "center", size=LAB + 2)
    f.text(cx + 33, cy, "<m>B</m>", "center", size=LAB + 2)
    return f.html()


def two_families():
    f = Fig(W4, 40)
    ax = f.axes(8, 3, W4 - 16, 32, xlim=(0, 6), ylim=(0, 1.0), frame=False)
    _curve(ax, stats.norm(2.0, 0.5), 0, 6, color=C.navy, width=2.6)
    x = np.linspace(0.01, 6, 300)
    ax.plot(x, stats.lognorm(0.6, 0, 1.6).pdf(x) * 1.25, color=C.sky, width=2.6)
    _base(f, 35)
    return f.html()


def propagate():
    """An input density, the formula f, and the density of the output:
    X ~ N(0, 1) through f(X) = exp(0.45 X), a lognormal."""
    f = Fig(W4, 52)
    axi = f.axes(0, 8, 76, 38, xlim=(-3, 3), ylim=(0, 0.42), frame=False)
    _curve(axi, stats.norm(), -3, 3, color=C.navy, width=2.4)
    f.line([(0, 46), (76, 46)], stroke=C.ink, width=1.4, cap="butt")
    m = W4 / 2
    f.rect(m - 34, 9, 68, 34, fill=C.navy)
    f.text(m, 26, "<m>f(X)</m>", "center", size=LAB, color=C.paper)
    f.arrow((82, 26), (m - 40, 26), color=C.ink, width=1.8)
    f.arrow((m + 38, 26), (W4 - 82, 26), color=C.ink, width=1.8)
    axo = f.axes(W4 - 76, 4, 76, 42, xlim=(0, 3.2), ylim=(0, 1.0), frame=False)
    x = np.linspace(0.01, 3.2, 300)
    axo.plot(x, stats.lognorm(0.45).pdf(x), color=C.accent, width=2.4)
    f.line([(W4 - 76, 46), (W4, 46)], stroke=C.ink, width=1.4, cap="butt")
    return f.html()


def demand_capacity(w=W4, h=54, labels=True):
    """Demand S ~ N(70, 8) and capacity R ~ N(100, 10) kN; the shaded area is
    where the two densities overlap."""
    f = Fig(w, h)
    ax = f.axes(4, 22, w - 8, h - 28, xlim=(40, 135), ylim=(0, 0.052), frame=False)
    x = np.linspace(40, 135, 400)
    d, c = stats.norm(70, 8).pdf(x), stats.norm(100, 10).pdf(x)
    ax.area(x, np.minimum(d, c), color=C.amber, opacity=0.55)
    ax.plot(x, d, color=C.accent, width=2.6)
    ax.plot(x, c, color=C.navy, width=2.6)
    _base(f, h - 6)
    if labels:
        X, _ = ax.P(70, 0)
        f.text(X - 30, 18, "demand", "south east", size=LAB)
        X, _ = ax.P(100, 0)
        f.text(X + 30, 18, "capacity", "south west", size=LAB)
    return f.html()


# ------------------------------------------------------------------ box 5
def point_regression():
    """A fitted line read at one x: the prediction Y-hat, one number."""
    f = Fig(W5, 40)
    ax = f.axes(8, 3, W5 - 16, 32, xlim=(0, 10), ylim=(0, 10), frame=False)
    ax.plot([0, 10], [6.0, 2.4], color=C.accent, width=2.6)
    x0 = 5.2
    y0 = 6.0 - 0.36 * x0
    ax.vline(x0, color=C.ink, width=1.6, dash="5 4", y0=0, y1=y0)
    ax.mark(x0, y0, r=6.5, color=C.paper, ring=C.accent, ring_w=2.5)
    X, Y = ax.P(0.25, 6.0)
    f.text(X, Y + 6, "<m>Ŷ</m>", "north west", size=LAB)
    X, Y = ax.P(x0, y0)
    f.text(X + 14, Y - 8, "<m>Ŷ</m>, one value", "south west", size=LAB)
    _base(f, 36)
    return f.html()


def point_design():
    """A density and one number read from it: the mean (a design value)."""
    f = Fig(W5, 52)
    ax = f.axes(8, 7, W5 - 16, 25, xlim=(-3.2, 3.2), ylim=(0, 0.42), frame=False)
    _curve(ax, stats.norm(), -3.2, 3.2, color=C.sky, width=2.6)
    ax.vline(0, color=C.ink, width=1.6, dash="5 4", y0=0, y1=0.3989)
    ax.mark(0, 0.3989, r=6.5, color=C.paper, ring=C.accent, ring_w=2.5)
    X, Y = ax.P(0, 0.3989)
    f.text(X + 12, Y - 2, "value", "south west", size=LAB)
    f.text(X, 52, "a design value", "south", size=LAB, cls="b")
    _base(f, 32)
    return f.html()


def point_beta():
    """The reliability index beta = 2.34 of his example (slide 38) against a
    target of 2.0."""
    f = Fig(W5, 44)
    ax = f.axes(8, 6, W5 - 16, 18, xlim=(0, 4), ylim=(0, 1), frame=False)
    ax.plot([0.1, 3.9], [0.5, 0.5], color=C.mist, width=7)
    ax.vline(2.0, color=C.ink, width=1.8, dash="5 4", y0=-0.4, y1=1.4)
    ax.mark(2.34, 0.5, r=6.5, color=C.accent)
    X, Y = ax.P(2.0, 0.5)
    f.text(X - 8, 44, "target", "south east", size=LAB)
    X2, _ = ax.P(2.34, 0.5)
    f.text(X2, 2, "<m>β</m>", "north", size=LAB, dx=16)
    f.text(X + 8, 44, "beta vs a target", "south west", size=LAB, cls="b")
    return f.html()


def prob_regression():
    """The chance the true value exceeds a limit: the prediction band of a
    fitted line and the part of it above the limit."""
    f = Fig(W5, 46)
    ax = f.axes(8, 3, W5 - 16, 40, xlim=(0, 10), ylim=(0, 10), frame=False)
    x = np.linspace(0, 10, 200)
    mu = 1.6 + 0.28 * x
    sd = 0.7 + 0.07 * x
    lo, hi = mu - 1.96 * sd, mu + 1.96 * sd
    lim = 5.4
    ax.area(x, hi, lo, color=C.mist)
    ax.area(x, np.maximum(hi, lim), lim, color=C.amber, opacity=0.6)
    ax.plot(x, mu, color=C.navy, width=2.4)
    ax.hline(lim, color=C.ink, width=1.8, dash="6 4")
    X, Y = ax.P(0.15, lim)
    f.text(X, Y - 3, "limit", "south west", size=LAB)
    X, Y = ax.P(2.4, lim)
    f.text(X, Y - 3, "<m>P(Y>limit)</m>", "south west", size=LAB)
    return f.html()


def prob_exceed():
    """A density and the chance of exceeding a value: the shaded upper tail."""
    f = Fig(W5, 40)
    ax = f.axes(8, 3, W5 - 16, 32, xlim=(-3.2, 3.2), ylim=(0, 0.42), frame=False)
    v = 1.1
    xs = np.linspace(v, 3.2, 120)
    ax.area(xs, stats.norm.pdf(xs), color=C.amber, opacity=0.6)
    _curve(ax, stats.norm(), -3.2, 3.2, color=C.sky, width=2.6)
    ax.vline(v, color=C.ink, width=1.6, dash="5 4", y0=0, y1=0.42)
    X, Y = ax.P(v, 0.02)
    f.text(X - 8, Y, "value", "south east", size=LAB)
    X, Y = ax.P(v, 0.30)
    f.text(X + 8, Y, "<m>P(X>value)</m>", "south west", size=LAB)
    _base(f, 38)
    return f.html()


def prob_shortfall():
    return demand_capacity(W5, 48)


def data_icon():
    """DATA: a handful of observations, 14 points of a correlated pair."""
    f = Fig(64, 64)
    f.rect(0, 0, 64, 64, fill=C.steel)
    x, y = sample(14, stats.norm(), stats.norm(), rho=0.5, skip=5)
    ax = f.axes(8, 8, 48, 48, xlim=(-2.4, 2.4), ylim=(-2.4, 2.4), frame=False)
    ax.scatter(x, y, r=3.6, color=C.navy)
    return f.html()
