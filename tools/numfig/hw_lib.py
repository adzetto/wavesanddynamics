"""The brochure's HOW IT WORKS flow: what its four icons share.

His four pictures (brochure-shm-and-ndt-2-pages, image1 to image4) are small
flat icons, navy line art with a gold accent, set at 82, 72, 92 x 76 and 74
CSS px between his arrows: Structure(s), Sensors on structure(s), Data
analysis, Decision making. Each is redrawn as a numfig page in the figures'
own line style (hw_structure.py, hw_sensors.py, hw_analysis.py,
hw_decision.py): navy and blue strokes, the crimson as the one accent, at his
size and proportion. The drawing unit is his CSS pixel (W = his width), so a
stroke is a whole number of device pixels and a line that runs straight sits
on the device pixel grid (snap()): crisp at one and at two device pixels to
the CSS pixel.

Each icon is QUIET (engine.js: it plays once, with no controls, and ignores
clicks). Icon k starts k x 0.35 s after it comes into view, so the four draw
left to right; each is drawn within a second, and its live part (the building
swaying in its first mode, the burst leaving the sensor, the record being
drawn and its peaks found) comes from the models below. The arrow after a
step is the page's (site/parts/docs.py): the icon before it hides it while
it waits off screen and lets it draw once its own first strokes are down,
before the next icon starts.

The building of Structure(s) and the record of Data analysis are one model:
a six storey shear frame set swaying in its first mode, in real time.
"""
import os

import numpy as np

import common

HERE = os.path.dirname(os.path.abspath(__file__))
SLUG = "brochure-shm-and-ndt-2-pages"
STAGGER = 0.35          # s between one icon's start and the next
ARROW_AT = 0.14         # s into an icon's own start: the arrow after it draws (0.22 s, done before the next)

# ------------------------------------------------------------------ the building (Structure(s), Data analysis)
N = 6                   # storeys (the icon's frame: 6 floors, 3 bays)
STOREY = 3.2            # m
CT = 0.075              # EN 1998-1 4.3.3.2.2(3): C_t of concrete moment resisting frames
MASS = 400e3            # kg per floor (a 20 x 20 m plan at 1 t/m2)
ZETA = 0.05             # EN 1998-1: the reference viscous damping, 5 %


def building():
    """The uniform shear building: N equal floors on N equal storeys, fixed at
    the ground, its first period from the code's T1 = C_t H^(3/4). Returns the
    storey stiffness, the modes (numerical and closed form) and the free
    vibration of the first mode, q(t) = exp(-zeta w1 t) sin(wd t)."""
    import scipy.linalg as sla

    H = N * STOREY
    T1 = CT * H ** 0.75
    w1 = 2 * np.pi / T1
    # closed form (Chopra, Dynamics of Structures, the uniform shear building):
    # w_r = 2 sqrt(k/m) sin((2r - 1) pi / (2 (2N + 1))), phi_jr = sin((2r - 1) j pi / (2N + 1))
    s1 = np.sin(np.pi / (2 * (2 * N + 1)))
    k = MASS * (w1 / (2 * s1)) ** 2
    K = np.zeros((N, N))
    for j in range(N):
        K[j, j] = 2 * k if j < N - 1 else k
        if j:
            K[j, j - 1] = K[j - 1, j] = -k
    M = MASS * np.eye(N)
    lam, Phi = sla.eigh(K, M)
    w = np.sqrt(lam)
    r = np.arange(1, N + 1)
    j = np.arange(1, N + 1)
    w_cf = 2 * np.sqrt(k / MASS) * np.sin((2 * r - 1) * np.pi / (2 * (2 * N + 1)))
    Phi_cf = np.sin(np.outer(j, 2 * r - 1) * np.pi / (2 * N + 1))
    phi = Phi[:, 0] / Phi[-1, 0]                       # the first mode, roof = 1
    wd = w1 * np.sqrt(1 - ZETA ** 2)
    return dict(H=H, T1=T1, w1=w1, wd=wd, a=ZETA * w1, k=k, K=K, M=M, w=w, Phi=Phi,
                w_cf=w_cf, Phi_cf=Phi_cf, phi=phi)


def q_first_peak(b):
    """The first maximum of exp(-a t) sin(wd t): at tan(wd t) = wd / a."""
    tp = np.arctan2(b["wd"], b["a"]) / b["wd"]
    return tp, np.exp(-b["a"] * tp) * np.sin(b["wd"] * tp)


# ------------------------------------------------------------------ the icons' shared script
JS = r"""
/* ---- the HOW IT WORKS icons (tools/numfig/hw_lib.py) ---- */
var QUIET = true;                                 // an icon: it plays once, no controls, no clicks
const S0 = DATA.k * %(stagger)s;                     // step k starts k x 0.35 s after it is seen
const at = (a, d) => seg(S0 + a, d);              // a stroke of this icon's intro, from its own start
const lands = (a, v = .28) => settle(S0 + a, v);  // a thing arriving, from its own start
/* whole device pixels: a stroke's width, and a coordinate on the grid for it */
const _dpu = () => cv.width / W;
function px(w) { const d = _dpu(); return Math.max(1, Math.round(w * d)) / d; }
function snap(v, w) { const d = _dpu(), n = Math.max(1, Math.round(w * d)); return (n %% 2 ? Math.floor(v * d) + .5 : Math.round(v * d)) / d; }
/* the flow's arrow after this step (site/parts/docs.py): hidden while this icon
   waits off screen, drawn once its own first strokes are down; in the page only */
const NEXT = (() => { try {
  const s = window.frameElement && frameElement.closest('.flow__step'), a = s && s.nextElementSibling;
  return a && a.classList.contains('flow__arrow') ? a : null; } catch (e) { return null; } })();
if (NEXT && !STILL && !REDUCED) {
  const r = NEXT.getBoundingClientRect(), vh = frameElement.ownerDocument.defaultView.innerHeight;
  if (r.bottom < 0 || r.top > vh) NEXT.classList.add('is-wait');
}
/* after each frame: the arrow's turn (once), and the end of the one play */
let _cued = false;
function cue(end) {
  if (NEXT && !_cued && t >= S0 + %(arrow)s) { _cued = true; NEXT.classList.add('is-in'); }
  if (playing && t >= end) setPlay(false);
}
""" % {"stagger": STAGGER, "arrow": ARROW_AT}


def publish(name, k, title, aria, w, h, data, js):
    """Write nf-hw-<name>.html (the icon's script after the shared one) and its
    still at his size, twice the pixels; return the still's PNG path."""
    common.build_html(f"hw-{name}", title, aria, w, h, {"k": k, **data}, JS + "\n" + js)
    return common.still(f"hw-{name}", width=w)


def write_check(name, lines):
    """tools/numfig/hw_<name>.check.txt, printed as well."""
    text = "\n".join(lines).rstrip() + "\n"
    print(text)
    with open(os.path.join(HERE, f"hw_{name}.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def overlap_lines(name, times):
    """The overlap check (README, "Nothing overlaps") at the poster and at
    `times`, as lines for the check file."""
    res = common.overlaps(f"hw-{name}", times)
    bad = {k: v for k, v in res.items() if v["labels"] or v["crossings"]}
    moments = ", ".join(k.replace("t=", "") + (" s" if k != "still" else "") for k in res)
    out = ["OVERLAP (common.overlaps, 672 px wide)", f"  moments: {moments}"]
    if bad:
        out += [f"  {k}: {v}" for k, v in bad.items()]
    else:
        out.append("  labels [] and crossings [] at every moment: nothing collides (the icon sets no type)")
    return out, not bad
