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


# ------------------------------------------------- additions among his figures
# (the professor's notes, 5 Oct 2026: new figures and words inside the signal
# processing guide's sections, its figures numbered again in turn)

def test_his_figure_numbers_move_in_one_pass():
    body = ('<figure><figcaption><span class="fign">Figure 2.</span> Adaptive.</figcaption></figure>'
            '<p>As in Figure 2 and Figure 3, but Figure 1 stays; Figures 3 and 12 too.</p>'
            '<figure><figcaption><span class="fign">Figure 3.</span> Landscapes.</figcaption></figure>')
    out = build.renumber(body, {"2": "3", "3": "8"})
    assert '<span class="fign">Figure 3.</span> Adaptive.' in out
    assert '<span class="fign">Figure 8.</span> Landscapes.' in out
    # 2 becoming 3 never meets 3 becoming 8, and other numbers stand
    assert "As in Figure 3 and Figure 8, but Figure 1 stays; Figures 8 and 12 too." in out
    assert build.renumber(body, {}) == body


def test_the_figures_must_read_in_turn_and_every_reference_must_land(monkeypatch):
    monkeypatch.setattr(build, "ANIM", {build.SIGNAL: {"x": {}}})
    cap = '<figure><figcaption><span class="fign">Figure {}.</span> x</figcaption></figure>'
    good = "".join(cap.format(k) for k in (1, 2, 3)) + "<p>See Figure 2 and Figure 3.</p>"
    assert build.numbered_in_turn(good, build.SIGNAL) == good
    with pytest.raises(SystemExit, match="do not read 1, 2, 3"):
        build.numbered_in_turn(cap.format(1) + cap.format(3), build.SIGNAL)
    with pytest.raises(SystemExit, match="figures the page does not have"):
        build.numbered_in_turn(good + "<p>Figure 9 shows</p>", build.SIGNAL)
    # a page drawn without its animations has no added figures to count
    monkeypatch.setattr(build, "ANIM", {})
    assert build.numbered_in_turn(cap.format(3), build.SIGNAL) == cap.format(3)


def test_an_addition_opens_a_section_or_follows_its_anchor_once():
    body = ('<h2>Blind Source Separation</h2><p>One topic I have not mentioned yet.</p>'
            '<p>In the language of Figure 1.</p><h2>Closing Thoughts</h2>')
    start, end, before = build._anchor(body, build.SIGNAL, {"after_heading": "Blind Source Separation"}, "t")
    assert body[:end].endswith("</h2>") and body[end:].startswith("<p>One topic") and not before
    start, end, before = build._anchor(body, build.SIGNAL, {"before_paragraph": "In the language"}, "t")
    assert before and body[start:].startswith("<p>In the language")
    with pytest.raises(SystemExit, match="finds 0 anchors"):
        build._anchor(body, build.SIGNAL, {"after_heading": "Blind Source"}, "t")   # whole words only


def test_added_words_are_held_to_the_sites_rules(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "ADDITIONS", str(tmp_path))
    (tmp_path / "ok.html").write_text(
        "<p>For this, I will get into details a bit: <tex>d = G m + e</tex>.</p>\n"
        "<h3>Kurtosis</h3>\n<tex display>\\hat{m} = \\arg\\min_{m} \\lVert G m - d \\rVert^2</tex>\n",
        encoding="utf-8")
    out = build._added_text(build.SIGNAL, "ok.html")
    assert "<math" in out and "<tex" not in out and "<h3>Kurtosis</h3>" in out
    (tmp_path / "dash.html").write_text("<p>One \u2014 two.</p>", encoding="utf-8")
    with pytest.raises(SystemExit, match="em dash"):
        build._added_text(build.SIGNAL, "dash.html")
    (tmp_path / "tag.html").write_text("<p>One <div>two</div>.</p>", encoding="utf-8")
    with pytest.raises(SystemExit, match="tags a passage of his does not use"):
        build._added_text(build.SIGNAL, "tag.html")


def test_a_figure_stands_where_the_new_text_marks_it(tmp_path, monkeypatch):
    """A figure entry "in_text" has no anchor: a block of new text marks its
    place (<!--figure:key-->), so a passage reads as written, paragraphs and
    figures in turn; every such figure is marked once."""
    import json
    monkeypatch.setattr(build, "ADDITIONS", str(tmp_path))
    (tmp_path / "a.html").write_text("<p>Before.</p>\n<!--figure:k1-->\n<p>After.</p>\n", encoding="utf-8")
    anim = {"src": "../anim/nf-x.html", "title": "X", "w": 1000, "h": 500,
            "still": {"src": "../anim/nf-x.webp", "w": 1344, "h": 672}}
    monkeypatch.setattr(build, "ANIM", {"doc": {"k1": anim}})
    supp = {"doc": [{"key": "k1", "in_text": True, "caption": "Figure 1a. A figure."},
                    {"html": "a.html", "after_paragraph": "His words"}]}
    monkeypatch.setattr(build, "ROOT", str(tmp_path / "root"))
    (tmp_path / "root" / "content" / "anim").mkdir(parents=True)
    (tmp_path / "root" / "content" / "anim" / "supplements.json").write_text(json.dumps(supp), encoding="utf-8")
    out = build.add_supplementary_figures("<p>His words.</p><p>His next.</p>", "doc")
    assert out.index("His words") < out.index("Before.") < out.index("nf-x.html") < out.index("After.") \
        < out.index("His next")
    assert '<figcaption><span class="fign">Figure 1a.</span> A figure.</figcaption>' in out
    # a figure no text marks, or a mark no entry holds, stops the build
    for bad in ([supp["doc"][0]], [{"html": "a.html", "after_paragraph": "His words"}]):
        (tmp_path / "root" / "content" / "anim" / "supplements.json").write_text(
            json.dumps({"doc": bad}), encoding="utf-8")
        with pytest.raises(SystemExit):
            build.add_supplementary_figures("<p>His words.</p>", "doc")
