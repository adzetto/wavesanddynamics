"""Figure 4a, wavelength of Figure 4's same SAFE branches and eigenvectors.

Run after dispersion.py --page. The second plot uses a logarithmic wavelength
axis (mm): lambda = 2 pi/k = 1000 c_p[km/s]/f[kHz]. Its data, solver,
packets and interactions are shared with the phase-velocity figure.
"""
import json
import re
from pathlib import Path

import common
import dispersion as d

NAME = "dispersion-wavelength"


def script():
    js = d.FIGURE
    replacements = {
        "PY = c => P.y + P.h - c / CM * P.h;":
            "PY = (c, f) => P.y + P.h - Math.log10(Math.max(1e-6, 1000 * c / Math.max(f, 1e-12))) / 4 * P.h;",
        "PY(Math.min(cp[i], 1.04 * CM))": "PY(cp[i], f[i])",
        "PY(Math.min(1.04 * CM, lerp(cpAtF(ba, f), cpAtF(bb, f), e)))": "PY(lerp(cpAtF(ba, f), cpAtF(bb, f), e), f)",
        "ylim: [0, CM]": "ylim: [0, 4]",
        "yticks: [0, 1, 2, 3, 4, 5, 6, 7]": "yticks: [0, 1, 2, 3, 4], yfmt: v => String(10 ** v)",
        "\\\\rm{phase velocity}\\\\ c_{\\\\rm{p}}\\\\ \\\\rm{(km/s)}": "\\\\rm{wavelength}\\\\ \\\\lambda\\\\ \\\\rm{(mm, log scale)}",
        "PY(s.cp)": "PY(s.cp, s.f)",
        "PY(lerp(cpAtF(ba, f), cpAtF(bb, f), e))": "PY(lerp(cpAtF(ba, f), cpAtF(bb, f), e), f)",
        "PY(A.cp)": "PY(A.cp, A.f)",
        "PY(B.cp)": "PY(B.cp, B.f)",
        "PY(q.cp)": "PY(q.cp, q.f)",
        "PY(S.cp)": "PY(S.cp, S.f)",
        "PY(S[w].cp)": "PY(S[w].cp, S[w].f)",
        "PY(LAST[v].cp)": "PY(LAST[v].cp, LAST[v].f)",
    }
    for old, new in replacements.items():
        assert old in js, old
        js = js.replace(old, new)
    # A straight phase-speed branch needs few points, but lambda=2pi/k is
    # curved. Refine in the displayed wavelength metric too, retaining the
    # original Hermite solution rather than joining sparse endpoints.
    old = "if (d < 14 && (Math.abs(wm - (w0 + w1) / 2)"
    assert old in js
    js = js.replace(old, "if (d < 14 && (Math.abs(Math.log10(km) - (Math.log10(k0) + Math.log10(k1)) / 2) * P.h / 4 > .2 || Math.abs(wm - (w0 + w1) / 2)")
    old = "line([[P.x, PY(c)], [P.x + P.w, PY(c)]], {color: C.guide, width: 1, dash: [5, 4], progress: seg(a0, .35)});"
    assert old in js
    js = js.replace(old, "line(Array.from({length: 201}, (_, i) => { const f = .001 * (FM / .001) ** (i / 200); return [PX(f), PY(c, f)]; }), {color: C.guide, width: 1, dash: [5, 4], progress: seg(a0, .35)});")
    # The legend identifies these curved reference wavelengths. Outside-axis
    # labels used for horizontal speed lines would be misleading here.
    js = re.sub(r"  math\('c_\{.*?\n", "", js, count=2)
    return "const D = DATA;\n" + d.SOLVER + js + "\nboot();\n"


def main():
    folder = Path(common.ANIM)
    source = (folder / "nf-dispersion.html").read_text(encoding="utf-8")
    data = json.loads(re.search(r"const DATA = (.*?);\n", source).group(1))
    for sec in data["secs"]:
        if sec["key"] != "bar":
            payload = (folder / f"nf-dispersion-{sec['key']}.json").read_bytes()
            (folder / f"nf-{NAME}-{sec['key']}.json").write_bytes(payload)
    common.build_html(NAME, "Figure 4a: Wavelength of guided waves against frequency",
                      "Wavelength in millimetres on a logarithmic vertical axis against frequency in kilohertz. "
                      "The same SAFE branches as Figure 4, with bar, I-beam, rail, pipe and plate choices. "
                      "Drag either wave marker to compare its wavelength and travelling packet.",
                      1000, 848, data, script())
    print(common.still(NAME))
    print(common.frames(NAME, [.6, 3, 20]))
    Path(__file__).with_suffix(".check.txt").write_text(
        "Figure 4a: the same meshes, curves, solver and wave packets as Figure 4.\n"
        "No second fitted dispersion relation: wavelength = 2 pi/k exactly.\n"
        "Units: k in rad/m, lambda in mm, f in kHz, c_p in km/s.\n"
        "1000 c_p/f = 2000 pi/k. At f = 50 kHz, c_p = 5 km/s: lambda = 100 mm.\n"
        "At k = 200 pi rad/m: lambda = 10 mm.\n"
        "The same branches and phase-velocity window as Figure 4 are retained for direct comparison.\n"
        "Curves are adaptively refined in log(lambda) to a midpoint chord error below 0.2 drawing units.\n"
        "Vertical range 1 to 10000 mm, logarithmic; lambda tends to infinity as k tends to zero.\n"
        "Poster and intro sampled by common.still, additional frames at 0.6, 3 and 20 s.\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
