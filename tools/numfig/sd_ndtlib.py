"""What the brochure's three NDT diagrams share (sd_ae.py, sd_pe.py, sd_img.py).

The brochure (brochure-shm-and-ndt-2-pages) draws three small pictures of
the same three techniques as Figure 3 of the SHM article: acoustic emission
(image6), pulse echo (image7) and imaging (image8). They are redrawn here as
three figures, each at its picture's proportions, from the model behind
nf-shm-ndt: shm_ndt.main() runs the 2D elastic model (shm_fdtd.py) and
returns every number the page draws (the recorded signal, the growth steps
and arrival times, the full matrix capture's image); it is imported, not
edited, and each figure takes its panel's share.

The script helpers below are the ones nf-shm-ndt's page uses (the burst,
the stealth tip, a beam cut from a longer member, a crack as a thin void),
so the four pictures read as one family.
"""
import functools

import numpy as np

import shm_ndt


@functools.lru_cache(maxsize=1)
def model():
    """shm_ndt's model and page data (cached runs in the temp directory):
    (data, check text, its locals)."""
    return shm_ndt.main()


def plain(o):
    """numpy scalars and arrays as plain JSON values."""
    if isinstance(o, dict):
        return {k: plain(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [plain(v) for v in o]
    if isinstance(o, np.ndarray):
        return plain(o.tolist())
    if isinstance(o, np.generic):
        return o.item()
    return o


PRELUDE = r"""
const D = DATA;
const lab = t0 => settle(t0, .28);
const rise = s => 4 * (1 - s);
const MASTER = D.master, US = D.us, CL = D.cl;
const phase = () => ((t % MASTER) + MASTER) % MASTER;
/* the burst the probes send, s(tau), tau in us from its start */
function burst(tau) {
  if (tau < 0 || tau > D.dur) return null;
  return Math.sin(2 * Math.PI * D.f0 * tau) * .5 * (1 - Math.cos(2 * Math.PI * D.f0 * tau / D.nc));
}
/* text and math in a row; returns the width */
function row(parts, x, y, o = {}) {
  const w = parts.reduce((s, [k, v]) => s + (k === 't' ? text(v, 0, -1e4, { ...o, alpha: 0 }) : math(v, 0, -1e4, { ...o, alpha: 0 })), 0);
  let cx = o.align === 'right' ? x - w : o.align === 'center' ? x - w / 2 : x;
  for (const [k, v] of parts) cx += k === 't' ? text(v, cx, y, { ...o, align: 'left' }) : math(v, cx, y, { ...o, align: 'left' });
  return w;
}
function tip(x, y, ang, color, size = 7, alpha = 1) {        // a TikZ stealth tip at (x, y)
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = color; ctx.beginPath(); ctx.moveTo(x, y);
  ctx.lineTo(x - size * Math.cos(ang - .38), y - size * Math.sin(ang - .38));
  ctx.lineTo(x - size * .62 * Math.cos(ang), y - size * .62 * Math.sin(ang));
  ctx.lineTo(x - size * Math.cos(ang + .38), y - size * Math.sin(ang + .38)); ctx.closePath(); ctx.fill(); ctx.restore();
}
/* a cut through a long member: the edge with a small zigzag in it */
function cutEdge(x, y0, y1, p, alpha = 1) {
  const m = (y0 + y1) / 2;
  line([[x, y0], [x, m - 8], [x - 5, m - 3], [x + 5, m + 3], [x, m + 8], [x, y1]], { color: C.ink, width: 1.2, progress: p, alpha });
}
function piece(x0, y0, w, h, p, o = {}) {                     // steel: fill, top face, back wall, cut ends
  const { cut = true } = o;
  if (p <= 0) return;
  ctx.save(); ctx.fillStyle = C.steel; ctx.fillRect(x0, y0, w * clamp(p), h); ctx.restore();
  line([[x0, y0], [x0 + w, y0]], { width: 1.7, progress: p });
  line([[x0, y0 + h], [x0 + w, y0 + h]], { width: 2.6, progress: p });
  if (cut) { cutEdge(x0, y0, y0 + h, p); cutEdge(x0 + w, y0, y0 + h, p); }
  else { line([[x0, y0], [x0, y0 + h]], { width: 1.7, progress: p }); line([[x0 + w, y0], [x0 + w, y0 + h]], { width: 1.7, progress: p }); }
}
function crackLine(p0, p1, half, alpha = 1, prog = 1) {       // a crack: a thin crimson void
  if (prog <= 0) return;
  const a = Math.atan2(p1[1] - p0[1], p1[0] - p0[0]), L = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]) * prog;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(p0[0], p0[1]); ctx.rotate(a);
  ctx.beginPath(); ctx.ellipse(L / 2, 0, L / 2, Math.max(half, 2), 0, 0, 2 * Math.PI);
  ctx.fillStyle = C.accent; ctx.fill(); ctx.strokeStyle = '#781E2C'; ctx.lineWidth = .9; ctx.stroke(); ctx.restore();
}
"""


def header(name, pic, words, what):
    """The check file's head: which picture, his words, the model."""
    return [
        f"{name}: the brochure's {pic} ({what}), redrawn from a model",
        f"generator: tools/numfig/{name.replace('nf-', '').replace('-', '_')}.py (helpers: sd_ndtlib.py);",
        "model: shm_ndt.main(), imported (tools/numfig/shm_ndt.py and shm_fdtd.py, Figure 3 of the SHM article);",
        "  the model's own validation is tools/numfig/shm_ndt.check.txt",
        "his words in the picture, kept verbatim: " + ", ".join(f'"{w}"' for w in words),
        "",
        "MODEL",
        "  2D plane-strain elastodynamics, velocity-stress on a staggered grid (Virieux 1986), voids as",
        "  cells of zero density and stiffness (EFIT, Fellinger et al. 1995); every face traction free.",
        "  steel: c_L = 5900 m/s, c_T = 3230 m/s, rho = 7850 kg/m3",
    ]
