"""Slide 32: his spring, Y = F/k mm, first against second order.

Inputs (his slide 26, the notes): F ~ N(100, 10^2) N and k lognormal with
mean 20 and SD 2 N/mm, independent. At the means: c_F = 1/20 = 0.05 mm/N,
c_k = -100/20^2 = -0.25 mm^2/N, sigma_Y^2 = (0.05 x 10)^2 + (-0.25 x 2)^2 =
0.5, sigma_Y = 0.707 mm; f_kk = 2F/k^3 = 0.025, so mu_Y = 5 + 1/2 (0.025)(2^2)
= 5.05 mm. Exact: E[1/k] = 1.01/20 and E[1/k^2] = 1.01^3/400 for this
lognormal (CV 0.1), so E[Y] = 5.050 mm and Var(Y) = 10100 x 1.01^3/400 - 5.05^2
= 0.5126 mm^2, SD 0.716 mm.

The picture holds F at 100 N and draws Y against k: the exact curve 100/k,
the tangent at k = 20 and the tangent plus curvature; the band is mu_k +- 2
sigma_k = 16 to 24 N/mm, the plausible inputs, as his."""
import numpy as np
from scipy import integrate, stats

from fig import Fig, C
from s031 import legend

MF, SF = 100.0, 10.0                        # N
MK, SK = 20.0, 2.0                          # N/mm, lognormal
S2 = np.log(1 + (SK / MK) ** 2)
KD = stats.lognorm(np.sqrt(S2), scale=MK * np.exp(-S2 / 2))
assert abs(KD.mean() - MK) < 1e-9 and abs(KD.std() - SK) < 1e-9

CF, CK = 1 / MK, -MF / MK ** 2
FKK = 2 * MF / MK ** 3
assert (CF, CK, FKK) == (0.05, -0.25, 0.025)
VAR1 = (CF * SF) ** 2 + (CK * SK) ** 2
assert abs(VAR1 - 0.5) < 1e-12 and round(np.sqrt(VAR1), 3) == 0.707
MEAN2 = MF / MK + 0.5 * FKK * SK ** 2
assert abs(MEAN2 - 5.05) < 1e-12

# the exact moments of F/k, by integration over k (F independent of k)
E1 = integrate.quad(lambda k: KD.pdf(k) / k, 0, np.inf)[0]
E2 = integrate.quad(lambda k: KD.pdf(k) / k ** 2, 0, np.inf)[0]
MEAN = MF * E1
SD = np.sqrt((MF ** 2 + SF ** 2) * E2 - MEAN ** 2)
assert f"{MEAN:.3f}" == "5.050" and f"{SD:.3f}" == "0.716"


def spring():
    f = Fig(832, 508)
    box, lim = (96, 8, 712, 396), dict(xlim=(9, 35), ylim=(1.0, 10.6))
    # the band first, then the axis on top of it (pgfplots' axis on top)
    f.axes(*box, frame=False, **lim).area([MK - 2 * SK, MK + 2 * SK], [10.6, 10.6], 1.0, color=C.steel)
    ax = f.axes(*box, xticks=range(10, 36, 5), yticks=range(2, 11, 2), grid=True,
                xlabel="Stiffness <m>k</m> (N/mm), fixed <m>F = 100</m> N",
                ylabel="<m>Y</m> (mm)", **lim)
    k = np.linspace(10, 34, 600)
    d = k - MK
    ax.plot(k, MF / MK + CK * d, color=C.accent, width=3.5, dash="12 8")
    ax.plot(k, MF / MK + CK * d + 0.5 * FKK * d ** 2, color=C.blue, width=4.5, dash="0.1 9")
    ax.plot(k, MF / k, color=C.navy, width=4.5)
    ax.mark(MK, MF / MK, r=8, color=C.navy)
    legend(f, ax.x + ax.w - 14, ax.y + 14, [
        ("Exact nonlinear response", {"color": C.navy, "width": 4.5}),
        ("First order: tangent", {"color": C.accent, "width": 3.5, "dash": "12 8"}),
        ("Second order: curvature", {"color": C.blue, "width": 4.5, "dash": "0.1 9"}),
    ], anchor="north east")
    return f.html()
