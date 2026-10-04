"""Scientific limits and placement guards for the additional worked examples."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "site"))
sys.path.insert(0, str(ROOT / "tools" / "numfig"))
import build
import preview
import dispersion as d


def test_plate_basis_represents_infinite_width_and_exact_sh_speed():
    model = d.make_section("plate")
    k = 200.
    w, v = model.solve("SHs", k, 1)
    assert w[0] / k == pytest.approx(d.sm.C_T, rel=1e-9)
    u = v[:, 0].reshape(-1, 3)
    assert np.max(abs(u[:, [0, 2]])) < 1e-12
    # Nodes at the same thickness coordinate move together. There are no
    # finite-width edge modes in this representation of an infinite plate.
    for z in np.unique(model.nodes_mm[:, 1]):
        rows = u[model.nodes_mm[:, 1] == z]
        assert np.max(abs(rows - rows[0])) < 1e-12


def test_plate_s0_limit_is_plane_stress_extension():
    model = d.make_section("plate")
    exact = np.sqrt(d.sm.E / (d.sm.RHO * (1 - d.sm.NU**2)))
    assert model.omegas("S", 2., 1)[0] / 2 == pytest.approx(exact, rel=1e-5)


def test_section_switching_needs_no_external_data_requests():
    import json
    import re
    for name in ["dispersion", "dispersion-wavelength"]:
        source = (ROOT / "content/anim" / f"nf-{name}.html").read_text(encoding="utf-8")
        data = json.loads(re.search(r"const DATA = (.*?);\n", source).group(1))
        assert set(data["blobs"]) == set(d.ORDER)
        assert all(data["blobs"].values())
        assert "fetch(" not in source


def test_supplement_anchor_is_required_once(monkeypatch):
    monkeypatch.setattr(build, "ANIM", preview.animations())
    with pytest.raises(SystemExit, match="finds 0 anchors"):
        build.add_supplementary_figures("<p>No figure here</p>", build.WAVES)
    fig = "<figure><figcaption>Figure 4. Original</figcaption></figure>"
    with pytest.raises(SystemExit, match="finds 2 anchors"):
        build.add_supplementary_figures(fig + fig, build.WAVES)


def test_new_examples_keep_print_and_full_screen_fallbacks(monkeypatch):
    monkeypatch.setattr(build, "ANIM", preview.animations())
    for slug, names in [(build.WAVES, ["dispersion-wavelength"]),
                        (build.ML, ["ml-feature-selection", "ml-forecasting"])]:
        page = build.page_doc(slug)
        for name in names:
            assert f'../anim/nf-{name}.html"' in page
            assert f'../anim/nf-{name}.webp"' in page
        assert "anim__full" in page
    ml = build.page_doc(build.ML)
    assert ml.index("nf-ml-forecasting.html") < ml.index("Clustering is unsupervised")
    assert ml.index("Embedded methods") < ml.index("nf-ml-feature-selection.html")
    assert ml.index("nf-ml-feature-selection.html") < ml.index('<h2 id="non-neural-network-models"')
