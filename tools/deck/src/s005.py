"""Slide 5: the M/M/1 queue of his notes. Poisson arrivals, exponential
service with mean 1/mu = 5 min, one server, steady state at utilization
rho = lambda/mu < 1: the mean wait in the queue is Wq = rho/(mu - lambda)
= 5 rho/(1 - rho) min. His three utilizations 0.5, 0.8 and 0.9 give 5, 20
and 45 min. The dashed guide is rho = 1, where the mean wait has no bound."""
import numpy as np

from fig import Fig, C

S = 5.0                                   # mean service time, min


def wq(rho):
    return S * rho / (1 - rho)


RHO = np.array([0.5, 0.8, 0.9])
assert np.allclose(wq(RHO), [5, 20, 45])


def wait():
    f = Fig(976, 616)
    ax = f.axes(120, 14, 838, 468, xlim=(0, 1.04), ylim=(-2.5, 65),
                xticks=[0, 0.2, 0.4, 0.6, 0.8, 1], yticks=range(0, 61, 10),
                xlabel="Utilization = arrival rate / service rate",
                ylabel="Mean waiting time (min)", grid=True)
    ax.vline(1.0)
    top = 65 / (65 + S)                   # where the curve leaves the box
    rho = np.concatenate([np.linspace(0, 0.9, 600), np.linspace(0.9, top + 0.002, 300)])
    ax.plot(rho, wq(rho), color=C.accent, width=4.5)
    for r in RHO:
        ax.mark(r, wq(r), r=10, color=C.navy)
    return f.html()
