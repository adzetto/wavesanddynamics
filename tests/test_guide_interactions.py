"""Independent checks for the interactive building's eigensolver and FFT."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pytest
import scipy.linalg as sla

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/numfig'))
import building
import dispersion


def test_browser_stiffness_solver_and_spectrum_against_scipy():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node unavailable')
    R = building.compute()
    D = {key: R[key].tolist() for key in ['m', 'k']}
    D['v0'] = float(R['v0'])
    factors = [[1.] * 5, [.2] * 5, [1.5] * 5]
    factors += [list(np.where(np.arange(5) == i, .55, 1.)) for i in range(5)]
    factors += np.random.default_rng(52).uniform(.2, 1.5, (20, 5)).tolist()
    js = building.JS.split('function solveStiffness', 1)[1].split('/* ---------------------------------------------------------------- drawing */')[0]
    harness = 'const N=5,D=' + json.dumps(D) + ';\nfunction solveStiffness' + js
    harness += '\nconsole.log(JSON.stringify(' + json.dumps(factors) + '.map(f=>{let s=solveStiffness(f);return {...s,spectrum:fftSpectrum(s)};})));'
    result = subprocess.run([node, '-'], input=harness, text=True, capture_output=True, check=True)
    models = json.loads(result.stdout)
    for fac, model in zip(factors, models):
        M, K = building.matrices(R['m'], R['k'] * fac)
        w, phi = building.modes(M, K)
        assert np.allclose(model['w'], w, rtol=1e-11)
        pj = np.asarray(model['phi']).T
        assert np.allclose(pj.T @ M @ pj, np.eye(5), atol=1e-12)
        assert np.allclose(K @ pj, (M @ pj) * np.asarray(model['w'])**2, rtol=1e-9, atol=1e-7)
        # Every case has the same initial roof velocity/impulse.
        assert np.allclose(pj @ (np.asarray(model['Q']) * model['w']), [0, 0, 0, 0, R['v0']], atol=1e-12)
        tt = np.arange(2048) / 64
        q = phi[-1] * R['m'][-1] * R['v0'] / w
        roof = 1000 * np.sum((q * phi[-1])[:, None] * np.sin(w[:, None] * tt), axis=0)
        window = np.hanning(2048)
        amp = abs(np.fft.rfft(roof * window)) * 2 / window.sum()
        amp[[0, -1]] *= .5
        actual = np.asarray(model['spectrum'])
        assert np.allclose(actual[:, 0], np.fft.rfftfreq(2048, 1/64))
        assert np.allclose(actual[:, 1], amp, atol=1e-10)


def test_refined_bar_mesh_matches_reference_dimensions():
    nodes, elems = dispersion.bar_mesh()
    assert len(elems) == 16 * 32
    assert len(nodes) == 33 * 65
    assert np.max(np.diff(np.unique(nodes[:, 0]))) == pytest.approx(.625)


def test_sparse_eigenpairs_match_independent_dense_solution():
    model = dispersion.make_section('bar', .5)
    w, _ = dispersion.sparse_modes(model, 'vertical', 150., 8)
    _, k1, k2, k3, m = model.cls('vertical')
    ref = np.sqrt(sla.eigh(k1 + 150*k2 + 150**2*k3, m,
                         eigvals_only=True, subset_by_index=[0, 7]))
    assert np.allclose(w, ref, rtol=1e-9)
