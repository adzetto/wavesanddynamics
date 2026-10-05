"""Figure 4a, wavenumber of Figure 4's same SAFE branches and eigenvectors.

Run after dispersion.py --page. The plot's vertical axis is the wavenumber
(rad/m, logarithmic): k = 2 pi f/c_p of every point of Figure 4's curves,
each section over its own frequency window (its published curves' range).
Its data (all five sections, inside the page), solver, packets, clock and
interactions are Figure 4's; only the vertical mapping changes.
"""
import json
import re
from pathlib import Path

import common
import dispersion as d

NAME = "dispersion-wavelength"
KLOG = 3              # decades shown: 1 to 1000 rad/m


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
        "\\\\rm{phase velocity}\\\\ c_{\\\\rm{p}}\\\\ \\\\rm{(km/s)}": "\\\\rm{wavenumber}\\\\ k\\\\ \\\\rm{(rad/m, log scale)}",
        "PY(s.cp)": "PY(s.cp, s.f)",
        "PY(A.cp)": "PY(A.cp, A.f)",
        "PY(B.cp)": "PY(B.cp, B.f)",
        "PY(q.cp)": "PY(q.cp, q.f)",
        "PY(S.cp)": "PY(S.cp, S.f)",
        "PY(S[w].cp)": "PY(S[w].cp, S[w].f)",
        "PY(LAST[v].cp)": "PY(LAST[v].cp, LAST[v].f)",
        # a straight phase-speed branch needs few points, but k = 2 pi f / c is curved: refine in the
        # displayed wavenumber metric too, keeping the Hermite solution rather than joining sparse ends
        "if (d < 14 && (Math.abs(wm - (w0 + w1) / 2)":
            "if (d < 14 && (Math.abs(Math.log10(km) - (Math.log10(k0) + Math.log10(k1)) / 2) * P.h / %d > .2 || "
            "Math.abs(wm - (w0 + w1) / 2)" % KLOG,
        # the shear and Rayleigh speeds become the wavenumbers 2 pi f / c_T and 2 pi f / c_R across the window
        "line([[P.x, PY(c)], [P.x + P.w, PY(c)]], {color: C.guide, width: 1, dash: [5, 4], progress: seg(a0, .35)});":
            "line(Array.from({length: 201}, (_, i) => { const f = WIN.fm * 1e-3 ** (1 - i / 200); return [PX(f), PY(c, f)]; }),"
            " {color: C.guide, width: 1, dash: [5, 4], progress: seg(a0, .35)});",
    }
    for old, new in replacements.items():
        assert old in js, old
        js = js.replace(old, new)
    # the legend names the curved reference wavenumbers: the speeds' names at the frame's edge go
    js = re.sub(r"  math\('c_\{\\\\rm\{[TR]\}\}'.*?\n", "", js, count=2)
    assert "math('c_{\\\\rm{T}}'" not in js and "math('c_{\\\\rm{R}}'" not in js
    left = [js[m.start():m.start() + 40] for m in re.finditer(r"\bPY\(", js) if not _two_args(js, m.end())]
    assert not left, f"vertical positions left in c_p alone: {left}"
    return "const D = DATA;\n" + d.SOLVER + js + "\nboot();\n"


TITLE = "Figure 4a: Wavenumber of guided waves against frequency"
ARIA = ("Wavenumber in radians per metre on a logarithmic vertical axis against frequency in kilohertz: the same "
        "SAFE branches as Figure 4 for a square bar, an IPE 80 I-beam, a 60E1 rail, a schedule 40 pipe and a plate, "
        "each over its own frequency range as in Figure 4. Two wave markers can be dragged along the curves to "
        "compare their wavenumbers and travelling packets.")


def main():
    folder = Path(common.ANIM)
    source = (folder / "nf-dispersion.html").read_text(encoding="utf-8")
    data = json.loads(re.search(r"const DATA = (.*?);\n", source).group(1))
    assert set(data["blobs"]) == set(d.ORDER)          # every section inside the page: nothing fetched
    common.build_html(NAME, TITLE, ARIA, 1000, d.HEIGHT, data, script())
    print(common.still(NAME))
    ov = common.overlaps(NAME, [.6, 3, d.POSTER, 20])
    bad = {k: v for k, v in ov.items() if v["labels"] or v["crossings"]}
    # every section, through its tour, its switches held half way, and live with the controls (Figure 4's check)
    name0, d.NAME = d.NAME, NAME
    try:
        moments = [.9, d.POSTER, 20, 29, 40, 47, 65]
        secs = d.overlaps_all(moments)
        live = d.overlaps_all([.9, d.POSTER, 20, 29, 40], live=True)
    finally:
        d.NAME = name0
    bad.update({f"{k} {m}": v for k, ms in secs.items() for m, v in ms.items() if v})
    bad.update({f"live {k} {m}": v for k, ms in live.items() for m, v in ms.items() if v})
    print("overlaps:", bad or "none")
    print(common.frames(NAME, [.6, 3, 20]))
    secs = ", ".join(f"{d.SECTIONS[k]['label']} 0 to {d.SECTIONS[k]['fmax'] / 1e3:g} kHz" for k in d.ORDER)
    size = (folder / f"nf-{NAME}.html").stat().st_size
    Path(__file__).with_suffix(".check.txt").write_text(
        "Figure 4a: the same meshes, curves, solver, wave packets and clocks as Figure 4 (nf-dispersion.html's\n"
        "data, all five sections inside the page: nothing is fetched).\n"
        "No second fitted dispersion relation: k = 2 pi f/c_p exactly, at every point of Figure 4's curves.\n"
        "Units: k in rad/m, f in kHz, c_p in km/s.\n"
        "At f = 50 kHz and c_p = 5 km/s: k = 62.832 rad/m.\n"
        f"Each section over its own frequency window, as in Figure 4: {secs}; the same branches\n"
        "(Figure 4's count, checked there against each section's reference) and Figure 4's phase-velocity window\n"
        f"(c_p up to {d.CP_MAX / 1e3:g} km/s), so a branch begins where it enters that window, not at k = 0.\n"
        "The shear and Rayleigh references become the curves k = 2 pi f/c_T and 2 pi f/c_R.\n"
        "Curves are adaptively refined in log(k) to a midpoint chord error below 0.2 drawing units.\n"
        f"Vertical range 1 to {10 ** KLOG} rad/m, logarithmic; k tends to zero as frequency tends to zero.\n"
        f"Overlaps (engine ?overlap): the bar at the poster and t = 0.6, 3, {d.POSTER:.2f} and 20 s; every section at\n"
        f"t = {', '.join(f'{m:g}' for m in moments)} s with every switch held at 30, 60 and 85 %, and live (the controls\n"
        f"drawn) at 5 moments: {'none' if not bad else sorted(bad)}.\n"
        f"Page {size / 1024:.0f} KB. Poster and intro sampled by common.still, frames at 0.6, 3 and 20 s.\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
