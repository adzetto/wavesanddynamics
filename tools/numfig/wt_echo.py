"""The fun table, "Pulse and echo" (image10): an ultrasonic pulse, a flaw, a back wall.

Model: a contact probe (12 mm, 5 MHz, a 3 cycle Hann burst) on the face of
a steel block 60 mm long sends a pulse through it. A flaw (a 1.2 x 3.6 mm
void, 32 mm in) sends part of it back; the rest reaches the back wall and
returns. The probe records the A scan: the flaw echo at 2 x_f / c and the
back wall echo at 2 L / c, drawn under the block with time as depth c t / 2
so each echo sits under what sent it. The pulse is drawn as its fronts (the
incident plane front across the probe's width, the flaw's circular front,
the back wall's returning front), the echo amplitudes as a 2D FDTD run of
the same block gives them.

Run: python tools/numfig/wt_echo.py
"""
import numpy as np
from scipy.signal import hilbert

import wt_lib

NAME = "echo"

E, NU, RHO = 210e9, 0.29, 7850.0
C_L = np.sqrt(E * (1 - NU) / (RHO * (1 + NU) * (1 - 2 * NU)))
LEN = 0.060                                  # block length along the beam (m)
XF, FW, FH = 0.032, 0.0012, 0.0036           # flaw centre (along the beam), its width and height
APER, F0, NCYC = 0.012, 5e6, 3
SLOW = 1.2e5


def burst(t):
    T = NCYC / F0
    return np.where((t > 0) & (t < T), np.sin(np.pi * np.clip(t, 0, T) / T) ** 2 * np.sin(2 * np.pi * F0 * t), 0.0)


def fdtd(flaw=True, dx=6e-5):
    """2D scalar (longitudinal) wave FDTD of the block on a staggered grid (p at
    cell centres, v on faces). The back wall and the flaw are free (p = 0);
    the probe is a piston over its aperture on the front face (then at rest:
    rigid), the rest of that face free; above and below the beam an absorbing
    layer (the block is wide). Returns (t, p averaged over the probe's face)."""
    Ly = 0.030
    nx, ny = int(round(LEN / dx)), int(round(Ly / dx))
    x = (np.arange(nx) + 0.5) * dx; y = (np.arange(ny) + 0.5) * dx - Ly / 2
    X, Y = np.meshgrid(x, y, indexing="ij")
    void = np.zeros((nx, ny), bool)
    if flaw:
        void = ((X - XF) / (FW / 2)) ** 2 + (Y / (FH / 2)) ** 2 <= 1
    ap = np.abs(y) <= APER / 2
    dt = 0.9 * dx / (C_L * np.sqrt(2))
    Z = RHO * C_L
    npml = 60
    prof = np.zeros(ny)
    ramp = (np.arange(npml, 0, -1) / npml) ** 3
    prof[:npml] = ramp; prof[-npml:] = ramp[::-1]
    dp = np.exp(-0.25 * prof)[None, :]                       # per step damping in the layers
    dvy = np.exp(-0.25 * np.r_[prof[0], 0.5 * (prof[1:] + prof[:-1]), prof[-1]])[None, :]
    f4 = np.float32
    p = np.zeros((nx, ny), f4); vx = np.zeros((nx + 1, ny), f4); vy = np.zeros((nx, ny + 1), f4)
    dp, dvy = dp.astype(f4), dvy.astype(f4)
    kv, kp = f4(dt / (RHO * dx)), f4(dt * RHO * C_L ** 2 / dx)
    nt = int(2.35 * LEN / C_L / dt)
    rec = np.zeros(nt)
    for n in range(nt):
        vx[1:-1] -= kv * (p[1:] - p[:-1])
        vx[0] = np.where(ap, burst((n + 0.5) * dt) / Z, vx[0] - kv * 2 * p[0])   # piston, else free (ghost p = -p)
        vx[-1] += kv * 2 * p[-1]                                                  # back wall free (ghost p = -p)
        vy[:, 1:-1] -= kv * (p[:, 1:] - p[:, :-1])
        vy *= dvy
        p -= kp * ((vx[1:] - vx[:-1]) + (vy[:, 1:] - vy[:, :-1]))
        p[void] = 0.0
        p *= dp
        rec[n] = p[0, ap].mean()
    return (np.arange(nt) + 1) * dt, rec


lines = []
say = lines.append
say("nf-wt-echo: the fun table, 'Pulse and echo' (image10)")
say("")
say("MODEL")
say(f"  steel, c_L = sqrt(E (1 - nu) / (rho (1 + nu) (1 - 2 nu))) = {C_L:.1f} m/s; block {LEN*1e3:.0f} mm along the beam")
say(f"  probe {APER*1e3:.0f} mm, {F0/1e6:.0f} MHz, {NCYC} cycle Hann burst (wavelength {C_L/F0*1e3:.2f} mm);"
    f" flaw: a void {FW*1e3:.1f} x {FH*1e3:.1f} mm, {XF*1e3:.0f} mm in")
say(f"  echoes: flaw at 2 x_f / c = {2*(XF-FW/2)/C_L*1e6:.3f} us (its near face), back wall at 2 L / c ="
    f" {2*LEN/C_L*1e6:.3f} us")
say("")
say("CHECK: 2D FDTD of the longitudinal wave (scalar), 0.06 mm cells, the flaw and the back wall")
say("  free (p = 0), the probe a velocity source over its face; the record: p averaged over the probe")
TAG = f"echo{C_L:.3f}-{LEN}-{XF}-{FW}-{FH}-{APER}-{F0}-{NCYC}"        # the cache follows the model
t1, r1 = wt_lib.cached(TAG, fdtd, True)
t0, r0 = wt_lib.cached(TAG, fdtd, False)
dt = t1[1] - t1[0]
TP = NCYC / F0
bang = np.where(t1 < TP + 0.3e-6, r0, 0.0)            # the emitted pulse as the probe itself records it


def delay(sig, lo, hi):
    """Delay of the echo in [lo, hi] behind the recorded emission (cross correlation, sign free)."""
    seg = np.where((t1 > lo) & (t1 < hi), sig, 0.0)
    cc = np.correlate(seg, bang, "full")
    k = int(np.argmax(np.abs(cc))); cc = cc * np.sign(cc[k])
    y0, y1, y2 = cc[k - 1:k + 2]
    return (k - (len(bang) - 1) + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)) * dt


tf = 2 * (XF - FW / 2) / C_L
tb = 2 * LEN / C_L
d_f = delay(r1 - r0, tf - 0.6e-6, tf + TP + 0.6e-6)
d_b = delay(r0, tb - 0.6e-6, tb + TP + 0.6e-6)
amp = lambda sig, lo, hi: np.abs(hilbert(np.where((t1 > lo) & (t1 < hi), sig, 0.0))).max()
a_in = amp(r0, 0, TP + 0.3e-6)
a_f = amp(r1, tf - 0.6e-6, tf + TP + 0.6e-6)
a_b1, a_b0 = amp(r1, tb - 0.6e-6, tb + TP + 0.6e-6), amp(r0, tb - 0.6e-6, tb + TP + 0.6e-6)
say(f"  flaw echo, delay behind the recorded emission: {d_f*1e6:.3f} us, closed form 2 (x_f - w/2) / c ="
    f" {tf*1e6:.3f} us ({(d_f-tf)*1e9:+.0f} ns)")
say(f"  back wall echo (no flaw): {d_b*1e6:.3f} us, closed form 2 L / c = {tb*1e6:.3f} us ({(d_b-tb)*1e9:+.0f} ns)")
say("  the lag is the grid's own numerical dispersion (waves on a 20 cell per wavelength grid run")
say("  slow); the same scheme in 1D over the same 120 mm path, refined:")


def run1d(dx, S=0.9 / np.sqrt(2)):
    nx = int(round(LEN / dx)); dt1 = S * dx / C_L; Z = RHO * C_L
    p = np.zeros(nx); v = np.zeros(nx + 1)
    nt = int(2.2 * LEN / C_L / dt1); rec = np.zeros(nt)
    for n in range(nt):
        v[1:-1] -= dt1 / (RHO * dx) * (p[1:] - p[:-1])
        v[0] = burst((n + 0.5) * dt1) / Z
        v[-1] += dt1 / (RHO * dx) * 2 * p[-1]
        p -= dt1 * RHO * C_L ** 2 / dx * (v[1:] - v[:-1])
        rec[n] = p[0]
    t = (np.arange(nt) + 1) * dt1
    bang1 = np.where(t < TP + 0.3e-6, rec, 0.0)
    seg = np.where((t > tb - 0.6e-6) & (t < tb + TP + 0.6e-6), rec, 0.0)
    cc = np.correlate(seg, bang1, "full"); k = int(np.argmax(np.abs(cc))); cc = cc * np.sign(cc[k])
    y0, y1, y2 = cc[k - 1:k + 2]
    return (k - (len(bang1) - 1) + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)) * dt1


for dx in (60e-6, 30e-6, 15e-6):
    say(f"    {dx*1e6:3.0f} um cells: back wall echo {(wt_lib.cached(TAG + '1d', run1d, dx)-tb)*1e9:+6.1f} ns from 2 L / c")
say("  so the closed form times, which the drawing uses, are the converged ones.")
say(f"  echo envelopes against the emitted pulse's (2D): flaw {a_f/a_in:.3f}; back wall {a_b1/a_in:.3f}, without the"
    f" flaw {a_b0/a_in:.3f}")
say("  (the probe's face is rigid once it has fired, so an echo arrives doubled; the flaw shades the")
say(f"  back wall both ways; its own second echo, at {2*tf*1e6:.2f} us, is left out of the drawing)")
say("")
say("DRAWING")
say(f"  {LEN*1e3:.0f} mm = 700 units, the block drawn 20 mm deep to the same scale (the FDTD's is wide);")
say("  the A scan's time axis drawn as depth c t / 2 on the same scale;")
say("  the A scan is drawn rectified (its envelope, the Hann window of each burst: 5 MHz cycles are finer")
say("  than the drawing), at the closed form times with the 2D FDTD's amplitudes; the fronts in the")
say("  block are the geometric wavefronts at the same times.")
say(f"  time slowed {SLOW:.1e} x: the back wall echo returns {tb*1e6:.1f} us after the pulse, {tb*SLOW:.2f} s on screen.")
wt_lib.write_check(NAME, lines)

DATA = {"c": C_L, "L": LEN, "xf": XF, "fw": FW, "fh": FH, "ap": APER, "f0": F0, "n": NCYC, "slow": SLOW,
        "af": float(a_f / a_in), "ab": float(a_b1 / a_in)}

JS = r"""
const PX = 150, SC = 700 / DATA.L, XC = x => PX + x * SC;  // the probe face at PX; metres to units
const YT = 24, YB = YT + .020 * SC, YM = (YT + YB) / 2;    // the block, 20 mm deep, to scale
const TY = 372, TA = 84;                                  // the A scan's zero line and height
const c = DATA.c, slow = DATA.slow, TB = 2 * DATA.L / c, TF = 2 * (DATA.xf - DATA.fw / 2) / c;
const LOOP = TB * slow + 1.3;
const U0 = TB * slow + .35, POSTER_T = 0;               // t = 0 (and the still): both echoes recorded
const TP = DATA.n / DATA.f0;
const env = s => (s > 0 && s < TP) ? Math.pow(Math.sin(Math.PI * s / TP), 2) : 0;
function ascan(s) { return env(s) + DATA.af * env(s - TF) + DATA.ab * env(s - TB); }   // rectified: the envelopes
function draw() {
  const u = wrap(U0 + t, LOOP), tau = u / slow;   // model time since the pulse left
  const aS = 1, k = clamp(1 - (u - (LOOP - .4)) / .35);
  // the block, its back wall heavier, the flaw
  ctx.save(); ctx.globalAlpha *= aS; ctx.fillStyle = C.steel; ctx.fillRect(PX, YT, XC(DATA.L) - PX, YB - YT); ctx.restore();
  line([[XC(DATA.L), YT], [PX, YT], [PX, YB], [XC(DATA.L), YB]], { color: C.ink, width: SW.struct });
  line([[XC(DATA.L), YT], [XC(DATA.L), YB]], { color: C.ink, width: SW.struct + 4, alpha: aS });
  ctx.save(); ctx.beginPath();
  ctx.ellipse(XC(DATA.xf), YM, DATA.fw / 2 * SC, DATA.fh / 2 * SC, 0, 0, 2 * Math.PI);
  ctx.fillStyle = C.accent; ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = '#781E2C'; ctx.stroke(); ctx.restore();
  // the fronts: incident across the probe's width, the flaw's circle, the back wall's return
  ctx.save(); ctx.beginPath(); ctx.rect(PX, YT, XC(DATA.L) - PX, YB - YT); ctx.clip();
  const ha = DATA.ap / 2 * SC, xi = c * tau;
  if (tau > 0 && xi < DATA.L) line([[XC(xi), YM - ha], [XC(xi), YM + ha]], { color: C.blue, width: SW.data, alpha: k });
  const xr = 2 * DATA.L - c * tau;
  if (xi > DATA.L && xr > 0) line([[XC(xr), YM - ha], [XC(xr), YM + ha]], { color: C.navy, width: SW.data, alpha: k });
  const rf = c * tau - (DATA.xf - DATA.fw / 2);
  if (rf > 0 && rf < DATA.xf) {
    ctx.save(); ctx.globalAlpha *= k * clamp(1.4 - rf / DATA.xf); ctx.strokeStyle = C.accent; ctx.lineWidth = SW.data - 1;
    ctx.beginPath(); ctx.arc(XC(DATA.xf - DATA.fw / 2), YM, rf * SC, Math.PI * .62, Math.PI * 1.38); ctx.stroke(); ctx.restore();
  }
  ctx.restore();
  // the probe on the front face
  line([[PX - 36, YM - ha - 6], [PX, YM - ha - 6], [PX, YM + ha + 6], [PX - 36, YM + ha + 6]], { color: C.navy, width: 2, fill: C.navy, close: true, alpha: aS });
  // the A scan: time drawn as depth c t / 2, so each echo sits under what sent it
  line([[PX, TY], [XC(DATA.L) + 20, TY]], { color: C.rule, width: SW.thin, alpha: aS });
  const n = 320, pts = [], fl = [];
  const tmax = Math.min(tau, TB + TP * 1.6);
  for (let i = 0; i <= n; i++) {
    const s = i / n * tmax, p = [PX + c * s / 2 * SC, TY - TA * ascan(s)];
    (s > TF - 1e-8 && s < TF + TP + 1e-8 ? fl : pts).push(p);
  }
  ctx.save(); ctx.globalAlpha *= k;
  const pre = pts.filter(p => p[0] <= PX + c * TF / 2 * SC + .5), post = pts.filter(p => p[0] >= PX + c * (TF + TP) / 2 * SC - .5);
  if (pre.length > 1) line(pre, { color: C.navy, width: SW.thin + 1 });
  if (fl.length > 1) line(fl, { color: C.accent, width: SW.data - 2 });
  if (post.length > 1) line(post, { color: C.navy, width: SW.thin + 1 });
  if (tau > 0) dot(PX + c * tmax / 2 * SC, TY - TA * ascan(tmax), 10, { color: C.navy, fill: C.navy });
  ctx.restore();
}
boot();
"""

TITLE = "Pulse and echo"
ARIA = ("An ultrasonic probe sends a pulse through a steel block; a flaw returns an early echo and "
        "the back wall a later one, and the recorded signal below shows each echo under the "
        "feature that sent it.")

if __name__ == "__main__":
    print(wt_lib.publish(NAME, TITLE, ARIA, DATA, JS))
