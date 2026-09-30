"""The system shared by the signal processing document's figures (sp_*.py).

One damped resonator, the textbook single degree of freedom structure, is the
system in Figure 1 (its convolution), Figure 2 (sampled, the unknown system an
adaptive filter identifies) and the cover (its natural frequency and damping
estimated from a noisy output):

    h(t) = exp(-zeta w_n t) sin(w_d t),   w_n = 2 pi f_n,   w_d = w_n sqrt(1 - zeta^2).

Convolutions are exact: an input given by its samples is taken piecewise
linear between them (first order hold), and the output samples of
y = x * h then follow from a complex first order recursion with no
quadrature error (foh_filter). check_page() evaluates expressions in a
figure's page, to compare the page's own arithmetic with numpy.
"""
import os

import numpy as np
from scipy.signal import lfilter

import common

FN, ZETA = 1.0, 0.10          # natural frequency (Hz), damping ratio


def pole(fn=FN, zeta=ZETA):
    """p = -zeta w_n + i w_d: h(t) = Im exp(p t)."""
    wn = 2 * np.pi * fn
    return complex(-zeta * wn, wn * np.sqrt(1 - zeta ** 2))


def h(t, fn=FN, zeta=ZETA):
    """The impulse response (zero before t = 0)."""
    p = pole(fn, zeta)
    t = np.asarray(t, float)
    return np.where(t >= 0, np.exp(p.real * t) * np.sin(p.imag * t), 0.0)


def foh_kernel(dt, fn=FN, zeta=ZETA):
    """g_0 and the constant C of the exact discrete kernel for an input that
    is linear between samples dt apart: y_n = sum_m g_{n-m} x_m with
    g_0 = Im (e^{p dt} - 1 - p dt)/(p^2 dt) and g_k = Im C e^{p k dt} (k >= 1),
    C = (e^{p dt} + e^{-p dt} - 2)/(p^2 dt)."""
    p = pole(fn, zeta)
    e = np.exp(p * dt)
    a0 = (e - 1 - p * dt) / (p * p * dt)
    cc = (e + 1 / e - 2) / (p * p * dt)
    return p, e, a0, cc


def foh_column(n, dt, fn=FN, zeta=ZETA):
    """The first column g_0 .. g_{n-1} of the lower triangular Toeplitz
    matrix A with (A x)_i = y(t_i) for the piecewise linear input."""
    p, e, a0, cc = foh_kernel(dt, fn, zeta)
    k = np.arange(n)
    g = (cc * np.exp(p * dt * k)).imag
    g[0] = a0.imag
    return g


def foh_filter(x, dt, fn=FN, zeta=ZETA):
    """Samples of y = x * h for x linear between its samples: exact."""
    p, e, a0, cc = foh_kernel(dt, fn, zeta)
    y = lfilter([a0, cc * e - a0 * e], [1, -e], np.asarray(x, float).astype(complex))
    return y.imag


def hann_pulse(t, c, w, a):
    """a sin^2 pulse centred at c, lasting w (zero outside)."""
    u = (np.asarray(t, float) - c) / w + 0.5
    return np.where((u > 0) & (u < 1), a * np.sin(np.pi * u) ** 2, 0.0)


def check_page(name, exprs):
    """Evaluate each JavaScript expression in nf-<name>.html (opened as a
    still, so nothing moves) and return the results as numpy arrays."""
    from playwright.sync_api import sync_playwright
    path = os.path.join(common.ANIM, f"nf-{name}.html").replace("\\", "/")
    out = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto("file:///" + path + "?still")
        pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
        for ex in exprs:
            out.append(np.array(pg.evaluate(ex), dtype=float))
        b.close()
    if errors:
        raise RuntimeError(f"nf-{name}: script errors: {errors}")
    return out
