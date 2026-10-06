"""Figure 4a, wavenumber of Figure 4's same SAFE branches and eigenvectors.

The plot's vertical axis is the wavenumber (rad/m, logarithmic, 1 to 1000): k = 2 pi f/c_p of
every point of Figure 4's curves, each section over its own frequency window (its published
curves' range), with the same branches as Figure 4 (each section's count, its reference's).
A branch cuts on at k -> 0, the bottom of this plot, so here every higher order branch is drawn
from its cut-on: below Figure 4's curve (which begins where its phase velocity falls under
10 km/s) comes its head, from under k = 1 rad/m up to that point, on wavenumbers refined in
this plot's own metric (dispersion.heads_of; Figure 4's points stay exactly Figure 4's). The
cut-on marks sit on the bottom frame, where those branches begin, and the legend names them.
The solver, packets, clock and interactions are Figure 4's; the vertical mapping, the window
(f up to the section's end and k from 1 rad/m) and the heads are this figure's own.

Run after dispersion.py (its sweeps cached in the temp folder; computed here otherwise).
"""
import json
import re
import time
from pathlib import Path

import numpy as np

import common
import dispersion as d

NAME = "dispersion-wavelength"
KLOG = 3              # decades shown: 1 to 1000 rad/m
assert d.K4A == 1.0   # the axis' bottom, where the heads begin


def _two_args(js, i):
    """Whether the call whose arguments start at js[i] has two (a comma outside any brackets)."""
    depth = 0
    for ch in js[i:]:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            if depth == 0:
                return False
            depth -= 1
        elif ch == "," and depth == 0:
            return True
    return False


def script():
    js = d.FIGURE
    # every vertical position is the wavenumber of (f kHz, c_p km/s): k = 2 pi f / c_p in rad/m
    replacements = {
        "PY = c => P.y + P.h - c / CM * P.h;":
            "PY = (c, f) => P.y + P.h - Math.log10(Math.max(1e-6, 2 * Math.PI * f / Math.max(c, 1e-12))) / %d * P.h;" % KLOG,
        "PY(Math.min(cp[i], 1.04 * CM))": "PY(cp[i], f[i])",
        "PY(Math.min(1.04 * CM, cpAtF(ba, u * A.fm)))": "PY(cpAtF(ba, u * A.fm), u * A.fm)",
        "PY(Math.min(1.04 * CM, cpAtF(bb, u * B.fm)))": "PY(cpAtF(bb, u * B.fm), u * B.fm)",
        "PY(cpAtF(ba, u * sw.from.fm))": "PY(cpAtF(ba, u * sw.from.fm), u * sw.from.fm)",
        "PY(cpAtF(bb, u * CUR.fm))": "PY(cpAtF(bb, u * CUR.fm), u * CUR.fm)",
        "ylim: [0, CM]": "ylim: [0, %d]" % KLOG,
        "yticks: [0, 2, 4, 6, 8, 10]": "yticks: [0, 1, 2, 3], yfmt: v => String(10 ** v)",
        "ylabelGap: 46": "ylabelGap: 50",
        "\\\\rm{phase velocity}\\\\ c_{\\\\rm{p}}\\\\ \\\\rm{(km/s)}": "\\\\rm{wavenumber}\\\\ k\\\\ \\\\rm{(rad/m, log scale)}",
        "PY(s.cp)": "PY(s.cp, s.f)",
        "PY(A.cp)": "PY(A.cp, A.f)",
        "PY(B.cp)": "PY(B.cp, B.f)",
        "PY(q.cp)": "PY(q.cp, q.f)",
        "PY(S.cp)": "PY(S.cp, S.f)",
        "PY(S[w].cp)": "PY(S[w].cp, S[w].f)",
        "PY(LAST[v].cp)": "PY(LAST[v].cp, LAST[v].f)",
        # a straight phase-speed branch needs few points, but k = 2 pi f / c is curved: refine in the
        # displayed wavenumber metric too, keeping the Hermite solution rather than joining sparse ends;
        # in c_p only where Figure 4 shows it (over the heads, where c_p runs to infinity, it is not drawn)
        "if (d < 14 && (Math.abs(wm - (w0 + w1) / 2) > tol * wm || Math.abs(wm / km - (w0 / k0 + w1 / k1) / 2) > tol * wm / km)) {":
            "if (d < 14 && (Math.abs(Math.log10(km) - (Math.log10(k0) + Math.log10(k1)) / 2) * P.h / %d > .2 || "
            "Math.abs(wm - (w0 + w1) / 2) > tol * wm || (wm / km <= CM && Math.abs(wm / km - (w0 / k0 + w1 / k1) / 2) > tol * wm / km))) {" % KLOG,
        # the shear and Rayleigh speeds become the wavenumbers 2 pi f / c_T and 2 pi f / c_R across the window
        "line([[P.x, PY(c)], [P.x + P.w, PY(c)]], {color: C.guide, width: 1, dash: [5, 4], progress: seg(a0, .35)});":
            "line(Array.from({length: 201}, (_, i) => { const f = WIN.fm * 1e-3 ** (1 - i / 200); return [PX(f), PY(c, f)]; }),"
            " {color: C.guide, width: 1, dash: [5, 4], progress: seg(a0, .35)});",
        # the window: up to the section's end, and from the bottom of the axis (each higher order branch from its cut-on)
        "const inWindow = (f, cp, k, fm) => f <= fm && cp <= CM;": "const inWindow = (f, cp, k, fm) => f <= fm && k >= %g;" % d.K4A,
        # the cut-on marks on the bottom frame, pointing up: each where its branch rises from k -> 0
        "const CUT = {y: P.y + 1, dir: 1};": "const CUT = {y: P.y + P.h - 1, dir: -1};",
        # named in the legend (the bottom frame has the branches' starts and the waves' thumbs beside it)
        "const E = [...sec.legend, ['guide', 'shear, Rayleigh']], cols = [];":
            "const E = [...sec.legend, ['guide', 'shear, Rayleigh'], ['cut', 'cut-on']], cols = [];",
    }
    for old, new in replacements.items():
        assert js.count(old) == 1, old
        js = js.replace(old, new)
    # no word over the frame: the legend names the marks
    m = re.search(r"function cutLabel\(sec, a\) \{\n.*?\n\}\n", js, re.S)
    assert m
    js = js[:m.start()] + "function cutLabel(sec, a) {}                    // (the legend names the cut-on marks)\n" + js[m.end():]
    # the legend names the curved reference wavenumbers: the speeds' names at the frame's edge go
    js = re.sub(r"  math\('c_\{\\\\rm\{[TR]\}\}'.*?\n", "", js, count=2)
    assert "math('c_{\\\\rm{T}}'" not in js and "math('c_{\\\\rm{R}}'" not in js
    left = [js[m.start():m.start() + 40] for m in re.finditer(r"\bPY\(", js) if not _two_args(js, m.end())]
    assert not left, f"vertical positions left in c_p alone: {left}"
    return "const D = DATA;\n" + d.SOLVER + js + "\nboot();\n"


TITLE = "Figure 4a: Wavenumber of guided waves against frequency"
ARIA = ("Wavenumber in radians per metre on a logarithmic vertical axis against frequency in kilohertz: the same "
        "SAFE branches as Figure 4 for a square bar, an IPE 80 I-beam, a 60E1 rail, a schedule 40 pipe and a plate, "
        "each over its own frequency range as in Figure 4, every higher order branch rising from its cut-on "
        "frequency at the bottom of the plot. Two wave markers can be dragged along the curves to compare their "
        "wavenumbers and travelling packets.")


def head_report(Rs, H):
    """Per section: the heads, their points, where they begin against the exact k = 0 cut-on
    frequency, and the thinned curve's error at every point (the page's own layout)."""
    rows = []
    for key in d.ORDER:
        Z, R = d.SECTIONS[key], Rs[key]
        brs, flat = d.curves_of(key, R)
        tb, tf, st = d.thinned(key, R, H[key])
        hi = [bi for bi, r in enumerate(brs) if not r["type"]]
        worst = 0.0
        for bi, (hk, hw) in H[key].items():
            name = Z["classes"][brs[bi]["ci"]][0]
            fc = float(R["cut"][name][brs[bi]["b"]])
            worst = max(worst, abs(hw[0] / (2 * np.pi) / fc - 1))
        kin = [bi for bi in hi if bi not in H[key]]
        rows.append(dict(key=key, n=len(brs), nh=len(hi), heads=len(H[key]), under=len(kin),
                         pts=sum(len(h[0]) for h in H[key].values()), kmin=min((h[0][0] for h in H[key].values()), default=0),
                         start=worst, kept=st["kept"], laid=st["laid"], err=st["err"]))
    return rows


def main():
    folder = Path(common.ANIM)
    t0 = time.time()
    Rs = {key: d.compute_section(key) for key in d.ORDER}
    H = {key: d.heads_of(key, Rs[key]) for key in d.ORDER}
    blobs = {key: d.section_blob(key, Rs[key], heads=True) for key in d.ORDER}
    js = script()
    data = d.page_data(blobs, js)
    assert set(data["blobs"]) == set(d.ORDER)          # every section inside the page: nothing fetched
    common.build_html(NAME, TITLE, ARIA, 1000, d.HEIGHT, data, js)
    print(common.still(NAME))
    ov = common.overlaps(NAME, [.6, 3, d.POSTER, 20])
    bad = {k: v for k, v in ov.items() if v["labels"] or v["crossings"]}
    # every section, through its tour, its switches held half way, and live with the controls (Figure 4's check)
    name0, d.NAME = d.NAME, NAME
    try:
        moments = d.tour_times()
        secs = d.overlaps_all(moments)
        live = d.overlaps_all([.9, d.POSTER, 20, 29, 40], live=True)
        pf = d.page_perf(rounds=2)
        swp = d.switch_perf(rounds=3)
    finally:
        d.NAME = name0
    bad.update({f"{k} {m}": v for k, ms in secs.items() for m, v in ms.items() if v})
    bad.update({f"live {k} {m}": v for k, ms in live.items() for m, v in ms.items() if v})
    print("overlaps:", bad or "none")
    print(common.frames(NAME, [.6, 3, 20]))
    rows = head_report(Rs, H)
    size = (folder / f"nf-{NAME}.html").stat().st_size
    secs_txt = ", ".join(f"{d.SECTIONS[k]['label']} 0 to {d.SECTIONS[k]['fmax'] / 1e3:g} kHz" for k in d.ORDER)
    L = ["Figure 4a (nf-dispersion-wavelength): the same meshes, branches, solver, wave packets and clocks as",
         "Figure 4 (all five sections inside the page: nothing is fetched), wavenumber on a logarithmic axis.",
         "No second fitted dispersion relation: k = 2 pi f/c_p exactly, at every point of the curves.",
         "Units: k in rad/m, f in kHz, c_p in km/s. At f = 50 kHz and c_p = 5 km/s: k = 62.832 rad/m.",
         f"Each section over its own frequency window, as in Figure 4: {secs_txt}.",
         "",
         "THE BRANCHES AND THE WINDOW",
         "  The same branches as Figure 4, so each section holds as many as its reference (Figure 4's count, checked",
         "  there: dispersion_branches.check.txt): those whose phase velocity falls under 10 km/s within the window.",
         "  A branch cuts on at k -> 0, which is the bottom of this plot, so here each higher order branch is drawn",
         f"  from its cut-on: 4a's window is f up to the section's end and k from {d.K4A:g} rad/m (the axis' bottom),",
         "  and a marker drags along the whole drawn curve. Below the point where Figure 4's curve begins (the sweep's",
         "  last point above 10 km/s) comes the branch's head: the sweep's own eigenvalues there and more between them,",
         "  each the same class's eigenvalue of the same index, until neighbours lie within 2 units in this plot's",
         "  metric (f over the window, log10 k over three decades, on 520 x 418 units, finer than the plot). The",
         "  heads are thinned for the cubic Hermite in k as Figure 4's curves are; Figure 4's own points follow",
         "  unchanged (the same travelling points, so the tour's wavenumbers are Figure 4's).",
         "  As in Figure 4, a branch that cuts on below a section's end but stays above 10 km/s until past it is",
         "  not drawn (the published figures have them only above their phase-velocity limit): " + "; ".join(
             f"{d.SECTIONS[k]['label']} " + ", ".join(f"{f / 1e3:.2f}" for f in d.undrawn(k, Rs[k])) + " kHz"
             for k in d.ORDER if d.undrawn(k, Rs[k])) + "; none in the others.",
         "  section  branches  higher order: with a head (points), under 1 rad/m already   first head point (k)"
         "   its f against the k = 0 cut-on"]
    for r in rows:
        L.append(f"  {d.SECTIONS[r['key']]['label']:7s}  {r['n']:3d}       {r['heads']:3d} ({r['pts']:5d}), {r['under']}"
                 f"                          {r['kmin']:.3f} rad/m            within {100 * r['start']:.3f} %")
    L += ["  The travelling curves at every point of the sweep and the heads (the page lays each segment out within",
          "  1e-5 in f, in log10 k within 0.2 units, and in c_p within 1e-5 where c_p is under 10 km/s):"]
    for r in rows:
        L.append(f"    {d.SECTIONS[r['key']]['label']:7s} {r['kept']} points travel, laid out as {r['laid']} (Python's layout):"
                 f" max |f_page/f - 1| = {r['err']:.1e}")
    L += ["  The cut-on marks sit on the bottom frame, pointing up, at the k = 0 frequency of each higher order branch",
          "  drawn (Figure 4's marks): where its head rises from the axis. The legend names them ('cut-on').",
          "  The shear and Rayleigh references become the curves k = 2 pi f/c_T and 2 pi f/c_R.",
          f"  Vertical range 1 to {10 ** KLOG} rad/m, logarithmic; k tends to zero as frequency tends to zero.",
          "",
          "THE PAGE",
          "  The first stop of the bar (the section the page opens on) is solved at build time by the page's own",
          "  script under node and carried in DATA; the other sections are made ready and the tour's coming states",
          "  solved while the page is idle or a frame leaves time (a few milliseconds at a time); the still parts",
          "  are kept as a picture once the intro is over (Figure 4's check file, PERFORMANCE)."]
    if pf:
        L.append("  In headless Chromium at 1280 x 800 CSS px, this shared machine (dispersion.page_perf: load, the longest")
        L.append("  task to 3 s; the script time of a frame held and gliding, median / 95th percentile / longest, and the")
        L.append("  longest task while gliding; render() at a held moment, 1280 / 672 px):")
        for tag, q_ in (("before (the page of 5 Oct 2026, commit e6205c0)", d.BEFORE_PERF.get(NAME)), ("now", pf)):
            if not q_:
                continue
            L.append(f"   {tag}:")
            for key in d.ORDER:
                if key in q_:
                    L.append(f"    {d.SECTIONS[key]['label']:7s} {d.perf_row(q_[key])}")
    L += d.switch_lines(d.BEFORE_SWITCH.get(NAME), swp)
    L += [f"Overlaps (engine ?overlap): the bar at the poster and t = 0.6, 3, {d.POSTER:.2f} and 20 s; every section at",
          f"{len(moments)} moments across its tour with every switch held at 30, 60 and 85 %, and live (the controls",
          f"drawn) at 5 moments: {'none' if not bad else sorted(bad)}.",
          f"Page {size / 1024:.0f} KB. Poster and intro sampled by common.still, frames at 0.6, 3 and 20 s.",
          f"(built in {time.time() - t0:.0f} s)"]
    Path(__file__).with_suffix(".check.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    if bad:
        raise RuntimeError("collisions: " + json.dumps(bad)[:3000])


if __name__ == "__main__":
    main()
