"""Slide 19: his Bayesian strength example, computed.

Normal prior mu ~ N(30, 2^2) MPa; normal data, n = 25 tests with known
sigma = 3 MPa and mean xbar = 32 MPa, so v_D = 3^2/25 = 0.36 MPa^2. The
posterior is normal with
  v_p = 1/(1/4 + 1/0.36) = 36/109 = 0.3303 MPa^2, SD 0.5747 MPa,
  m_p = (30/4 + 32/0.36)/(1/4 + 1/0.36) = 3470/109 = 31.8349 MPa,
the prior and data weights 9/109 = 0.0826 and 100/109 = 0.9174, and the 95%
credible interval 31.835 +- 1.96 x 0.575 = [30.71, 32.96] MPa (his notes).

The figure draws the prior, the likelihood of mu scaled to unit area (the
N(32, 0.36) density) and the posterior, with its 95% credible interval
shaded under it. His three long legend entries would cover the curves inside
the axes, so the legend stands over the plot, at the axes' left edge."""
import numpy as np
from scipy import stats

from fig import Fig, C
from s013 import legend

M0, V0, XBAR, VD = 30.0, 2.0 ** 2, 32.0, 3.0 ** 2 / 25
VP = 1 / (1 / V0 + 1 / VD)
MP = VP * (M0 / V0 + XBAR / VD)
W0, WD = VP / V0, VP / VD
LO, HI = MP - 1.96 * np.sqrt(VP), MP + 1.96 * np.sqrt(VP)
assert (V0, round(VD, 2), round(VP, 4), round(np.sqrt(VP), 3)) == (4.0, 0.36, 0.3303, 0.575)
assert (round(MP, 2), round(MP, 3), round(W0, 4), round(WD, 4)) == (31.83, 31.835, 0.0826, 0.9174)
assert (round(100 * W0), round(100 * WD)) == (8, 92)
assert (round(LO, 2), round(HI, 2)) == (30.71, 32.96)
assert np.isclose(MP, 3470 / 109) and np.isclose(VP, 36 / 109)
PRIOR, LIKE, POST = stats.norm(M0, np.sqrt(V0)), stats.norm(XBAR, np.sqrt(VD)), stats.norm(MP, np.sqrt(VP))


def posterior():
    f = Fig(832, 500)
    ax = f.axes(160, 138, 652, 270, xlim=(26, 36), ylim=(0, 0.75),
                xticks=[26, 28, 30, 32, 34, 36], yticks=[0, 0.2, 0.4, 0.6], ytick_nd=1,
                xlabel="Unknown population mean <m>μ</m> (MPa)",
                ylabel='<span style="display:block;text-align:center">Density / <br>scaled likelihood</span>',
                ylabel_gap=104)
    ci = np.linspace(LO, HI, 400)
    ax.area(ci, POST.pdf(ci), color=C.blue, opacity=0.18)
    x = np.linspace(26, 36, 1000)
    ax.plot(x, PRIOR.pdf(x), color=C.navy, width=3, dash="10 6")
    ax.plot(x, LIKE.pdf(x), color=C.accent, width=3.5)
    ax.plot(x, POST.pdf(x), color=C.blue, width=4.5)
    legend(ax, [("Prior: mean 30, SD 2", {"color": C.navy, "width": 3, "dash": "10 6"}),
                ("Likelihood (scaled to unit area)", {"color": C.accent, "width": 3.5}),
                ("Posterior: mean 31.83, SD 0.575", {"color": C.blue, "width": 4.5})],
           at=(160, 4), size=24, row=34, pad=14, sample=40, gap=10)
    return f.html()
