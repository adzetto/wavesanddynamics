"""Multi-objective optimization, Figure 2: the methods. Multicriteria decision
making (priori, posteriori, interactive) and the evolutionary algorithms,
each with his list and a sketch of how the method searches the objective
space.

His words are his, as he typed them ("EVALUATIONARY ALGORITHMS", "Goal
Atteintment", "Saticifing Tradeoff method", the MOGA line twice). His slide
set the four methods side by side; at the figures' 10 pt that is wider than
the post, so the decision making methods take two rows (priori and
posteriori, then interactive, whose sketch has the most to show) and the
algorithms a row of their own, each section under its heading and rule.

Every point of the sketches is computed in its own frame (P):
  priori       z_ref + a w, where the ray from z_ref along w first meets the
               feasible region (geom.hit);
  posteriori   F1* and F2*, the points of the region with the smallest F1 and
               F2, the Pareto Front between them (geom.front), and the ideal
               point (f1*, f2*) under both;
  interactive  indifference curves (F1 - U0)(F2 - V0) = k: u^{t-1} through A,
               and u^t, the highest that still meets the region, touching it
               at C'; D, C and B on the vertical through C';
  evolutionary a population drawn once from a seeded generator, each arrow
               pointing from it toward the front.
Every label is placed by its box, which TeX measures (geom.beside)."""
import numpy as np

from geom import Scene, beside, closed, front, hit, normal, pt, size, smooth

SLUG, STEM = "multi-objective-optimization", "fig2"
W = 462.0                                   # content width, pt
PITCH = 11.0                                # list line pitch (\small), pt
# rows, top down: heading and list baselines and the sketches' axis origins, pt
Y_MCDM, Y_SUB1, Y_LIST1, Y1 = 0.0, -21.0, -39.0, -176.5
Y_SUB2, Y_LIST2, Y2 = -214.0, -232.0, -364.0
Y_EA, Y_LIST3, Y3 = -410.0, -431.0, -519.5
SK = {"P": (20.0, Y1, 112.0, 84.0),         # sketch frames: axis origin x, y; axis lengths
      "Q": (262.0, Y1, 112.0, 84.0),
      "I": (226.0, Y2, 182.0, 116.0),
      "E": (238.0, Y3, 140.0, 84.0)}
LISTX = {"P": 0.0, "Q": 240.0, "I": 0.0, "E": 0.0}
BR = r"\\"                                # a line break in a node

PRIORI = ["Goal Programming", "Goal Atteintment", "Lexicographic method"]
POSTERIORI = ["Weighted Combinations", "Normal Boundary Interaction", "E-constraints",
              "Weighted Matrices"]
INTERACTIVE = ["Geoffrion-Dyer-Feinberg (GDF)", "Tchebycheff Method", "Reference Point Methods",
               "Light Beam Search", "Saticifing Tradeoff method", "NIMBUS"]
EVOLUTIONARY = ["Multi objective Genetic Algorithm (MOGA)", "Multi objective Genetic Algorithm (MOGA)",
                "SPEA and SPEA2", "PAES", "PASE"]


def P(name, u, v):
    """Fractions of a sketch's axes, in pt."""
    x0, y0, ax, ay = SK[name]
    return np.array([x0 + u * ax, y0 + v * ay])


def tp(name, U):
    """A TikZ path through fractions U of a sketch."""
    return " -- ".join(pt(*P(name, u, v)) for u, v in U)


def items(x, y, lines):
    out = []
    for k, s in enumerate(lines):
        yy = y - k * PITCH
        out.append(rf"\node[anchor=base west] at {pt(x, yy)} {{\small\textbullet}};")
        out.append(rf"\node[anchor=base west] at {pt(x + 9, yy)} {{\small {s}}};")
    return out


def list_width(lines):
    return 9 + max(size(rf"\small {s}")[0] for s in lines)


def heading(text, x, y, rule=None):
    """A heading (his words) with a line under it: under the words, or across rule = (x0, x1)."""
    w = size(text)[0]
    a, b = rule or (x - w / 2, x + w / 2)
    return [rf"\node[anchor=base] at {pt(x, y)} {{{text}}};",
            rf"\draw[fs thin] {pt(a, y - 2.6)} -- {pt(b, y - 2.6)};"]


def axes(name, S=None):
    """A sketch's axes and their labels, recorded in the Scene S if given."""
    o, xe, ye = P(name, 0, 0), P(name, 1, 0), P(name, 0, 1)
    if S is not None:
        for e in (xe, ye):
            S.line([o, e], 0.354)
            S.tip(o, e, 5.58, 2.5)
        w, h, d = size("$F_1(x, y)$")
        S.boxes.append((xe[0] + 2.5, xe[1] - (h + d) / 2, xe[0] + 2.5 + w, xe[1] + (h + d) / 2))
        w, h, d = size("$F_2(x, y)$")
        S.boxes.append((ye[0] - w / 2, ye[1] + 2.5, ye[0] + w / 2, ye[1] + 2.5 + h + d))
    return [rf"\draw[fs axis] {pt(*o)} -- {pt(*xe)};",
            rf"\draw[fs axis] {pt(*o)} -- {pt(*ye)};",
            rf"\node[fs axlabel, anchor=west] at {pt(xe[0] + 2.5, xe[1])} {{$F_1(x, y)$}};",
            rf"\node[fs axlabel, anchor=south] at {pt(ye[0], ye[1] + 2.5)} {{$F_2(x, y)$}};"]


def region(name, B):
    return [rf"\fill[fsBodyFill] {tp(name, B)} -- cycle;", rf"\draw[fs curve] {tp(name, B)} -- cycle;"]


# ------------------------------------------------------------------ priori
BP = closed([(0.43, 0.80), (0.48, 0.93), (0.62, 0.99), (0.80, 0.99), (0.93, 0.95), (0.95, 0.84),
             (0.90, 0.75), (0.94, 0.64), (0.93, 0.52), (0.84, 0.45), (0.72, 0.45), (0.66, 0.52),
             (0.62, 0.62), (0.53, 0.69), (0.45, 0.72)])
ZREF = np.array([0.46, 0.27])
WV = np.array([0.09, 0.225])                # w, drawn from the origin
_, HP = hit(BP, ZREF, WV)                   # z_ref + a w, on the region's edge


def priori():
    O, Wt, Z, H = P("P", 0, 0), P("P", *WV), P("P", *ZREF), P("P", *HP)
    L = axes("P") + region("P", BP)
    L += [rf"\draw[fs vec] {pt(*O)} -- {pt(*Wt)};",
          rf"\draw[fs vec] {pt(*O)} -- {pt(*Z)};",
          rf"\draw[fs vec] {pt(*Z)} -- {pt(*H)};",
          rf"\draw[fs vec aux] {pt(*O)} -- {pt(*H)};"]
    L.append(beside(Wt, (0, 1), "$w$", 2.0))
    L.append(beside(O + 0.76 * (Z - O), normal(O, Z, "right"), "$z^{ref}$", 2.2))
    L.append(beside(Z + 0.42 * (H - Z), normal(Z, H, "right"), "$aw$", 2.2))
    L.append(beside(O + 0.60 * (H - O), normal(O, H, "left"), "$z^{ref} + aw$", 2.2))
    return L


# ------------------------------------------------------------------ posteriori
BQ = closed([(0.25, 0.70), (0.28, 0.87), (0.37, 0.97), (0.51, 0.99), (0.64, 0.96), (0.70, 0.88),
             (0.73, 0.79), (0.82, 0.70), (0.90, 0.56), (0.91, 0.42), (0.86, 0.30), (0.77, 0.23),
             (0.62, 0.22), (0.46, 0.28), (0.33, 0.40), (0.27, 0.54)])
FQ = front(BQ)
F1S, F2S = BQ[FQ[0]], BQ[FQ[-1]]            # the smallest F1, the smallest F2
IDEAL = np.array([F1S[0], F2S[1]])


def posteriori():
    L = axes("Q") + region("Q", BQ)
    L.append(rf"\draw[fs heavy, line join=round] {tp('Q', BQ[FQ])};")
    L.append(rf"\draw[fs aux] {pt(*P('Q', F1S[0], 0))} -- {pt(*P('Q', *F1S))};")
    L.append(rf"\draw[fs aux] {pt(*P('Q', 0, F2S[1]))} -- {pt(*P('Q', *F2S))};")
    for p in (F1S, F2S, IDEAL):
        L.append(rf"\node[fs point] at {pt(*P('Q', *p))} {{}};")
    L.append(beside(P("Q", *F1S), (-0.6, 0.8), "$F_1^*$", 3.2))
    L.append(beside(P("Q", *F2S), (0.55, -0.83), "$F_2^*$", 3.2))
    L.append(beside(P("Q", F1S[0], 0), (0, -1), "$f_1^*$", 2.6))
    return L


# ------------------------------------------------------------------ interactive
BI = closed([(0.10, 0.48), (0.13, 0.68), (0.24, 0.84), (0.38, 0.93), (0.50, 0.96), (0.60, 0.955),
             (0.66, 0.93), (0.72, 0.86), (0.78, 0.77), (0.84, 0.66), (0.86, 0.56), (0.82, 0.45),
             (0.83, 0.34), (0.76, 0.22), (0.60, 0.15), (0.40, 0.14), (0.22, 0.19), (0.12, 0.32)])
U0, V0 = 0.241, 0.427                       # the indifference curves' asymptotes
AI = BI[np.argmin(np.hypot(*(BI - (0.84, 0.66)).T))]
K1 = (AI[0] - U0) * (AI[1] - V0)            # u^{t-1}(1), through A
_k = (BI[:, 0] - U0) * (BI[:, 1] - V0) * (BI[:, 0] > U0) * (BI[:, 1] > V0)
CP, K2 = BI[np.argmax(_k)], _k.max()        # C': where the highest curve u^t(1) touches the region
DI = np.array([CP[0], AI[1]])
CI = np.array([CP[0], V0 + K1 / (CP[0] - U0)])     # C: the vertical through C' meets u^{t-1}(1)
BI_TOP = 1.30                               # B, at the top of that vertical
SR = -0.19                                  # the slope of S_r through A, in the frame's fractions
assert K2 > K1 and DI[1] < CI[1] < CP[1]


def level(kk, v_top, u_end, n=90):
    u_top = U0 + kk / (v_top - V0)
    u = U0 + (u_top - U0) * np.geomspace(1, (u_end - U0) / (u_top - U0), n)
    return np.column_stack([u, V0 + kk / (u - U0)])


def interactive():
    """The sketch is crowded where A, C, C' and D meet: its strokes go into a
    Scene, and each label takes the nearest spot that keeps 2 pt from them."""
    def I(u, v):
        return P("I", u, v)
    x0, y0, ax, ay = SK["I"]
    A, D, C, Cp, B = I(*AI), I(*DI), I(*CI), I(*CP), I(CP[0], BI_TOP)
    S = Scene()
    L = axes("I", S) + region("I", BI)
    S.line([I(*b) for b in np.vstack([BI, BI[:1]])])

    def stroke(style, pts, width=0.354):
        S.line(pts, width)
        L.append(rf"\draw[{style}] " + " -- ".join(pt(*q) for q in pts) + ";")
    yd = y0 - 14.0                          # the dimension line under the axis
    stroke("fs aux", [(x0, A[1]), A])
    stroke("fs aux", [(D[0], yd - 4), B])
    stroke("fs aux", [(A[0], yd - 4), A])
    se = AI + 0.38 * (AI - (CP[0], BI_TOP)) / (BI_TOP - AI[1])        # S_e: from B through A, on
    stroke("fs aux", [B, I(*se)])
    l0 = CP[0] + 0.02 - AI[0]                # S_r starts just right of the vertical through D
    sr0, sr1 = AI + (l0, l0 * SR), AI + (0.27, 0.27 * SR)
    stroke("fs aux", [I(*sr0), I(*sr1)])
    c1, c2 = level(K1, 1.16, 1.12), level(K2, 1.30, 1.16)
    stroke("fs curve", [I(*q) for q in c1], 0.709)
    stroke("fs curve", [I(*q) for q in c2], 0.709)
    du, nn = I(*(AI + (0.09, 0.36))), I(*(AI + (0.21, 0.22)))
    for tipp in (du, nn):
        stroke("fs vec", [A, tipp], 0.709)
        S.tip(A, tipp)
    for q in (A, Cp):
        L.append(rf"\node[fs point] at {pt(*q)} {{}};")
        S.circle(q, 1.4)
    for a_, b_ in (((D[0] - 14, yd), (D[0], yd)), ((A[0] + 14, yd), (A[0], yd))):
        stroke("fs dim", [a_, b_])
        S.tip(a_, b_, 5.58, 2.5)
    # the labels, the most hemmed in first
    L.append(S.place("$C'$", Cp, (-1, -0.4), 2.0, need=1.8))
    L.append(S.place("$C$", C, (-1, -0.5), 2.0))
    L.append(S.place("$D$", D, (-0.8, -1), 2.0))
    L.append(S.place("$A$", A, (-0.75, -1), 2.0))
    L.append(S.place("$B$", B, (0, 1), 2.0))
    L.append(S.place("$u^{t-1}(1)$", I(*c1[0]), (-1, 0), 2.0))
    L.append(S.place(r"$u^t\,(1)$", I(*c2[0]), (-1, 0), 2.0))
    L.append(S.place(r"$\Delta u(X^{t-1})$", du, (0.35, 1), 2.0))
    L.append(S.place("$N^{t-1}$", nn, (1, 0.2), 2.0))
    L.append(S.place("$S_r^{t-1}$", I(*sr1), (0.3, -1), 2.0))
    L.append(S.place("$S_e^{t-1}$", I(*se), (1, -0.4), 2.0))
    L.append(S.place("$f_2^{t-1}$", (x0, A[1]), (-1, 0), 3.0))
    # the step on F1, a1 df1 = Delta f1, from D to A
    L.append(S.place(r"$a_1\,df_1^{t-1} = \Delta f_1^{t-1}$", (D[0] - 14, yd), (-1, 0), 2.5, "fs dimlabel"))
    L.append(S.place("$f_1^{t-1}$", (A[0] + 14, yd), (1, 0), 2.5, "fs dimlabel"))
    return L


# ------------------------------------------------------------------ evolutionary
FE = smooth([(0.08, 0.80), (0.12, 0.60), (0.19, 0.47), (0.27, 0.43), (0.33, 0.38), (0.36, 0.28),
             (0.39, 0.18), (0.46, 0.12), (0.60, 0.10), (0.72, 0.095)], 160)
UP = smooth([(0.72, 0.095), (0.88, 0.18), (0.98, 0.38), (1.01, 0.60), (0.94, 0.82), (0.75, 0.95),
             (0.47, 1.00), (0.21, 0.99), (0.09, 0.93), (0.08, 0.80)], 160)
CEN = np.array([0.54, 0.66])
RX, RY = 15.0, 11.5                         # the population's ellipse, pt


def population(n=18, seed=7):
    """n points in an ellipse about CEN, at least 4.4 pt apart: drawn once from a seeded generator."""
    c = P("E", *CEN)
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(20000):
        r, t = np.sqrt(rng.random()), rng.random() * 2 * np.pi
        p = c + (RX * r * np.cos(t), RY * r * np.sin(t))
        if all(np.hypot(*(p - o)) >= 4.4 for o in out):
            out.append(p)
            if len(out) == n:
                return np.array(out)
    raise AssertionError("the population does not fit its ellipse")


def evolutionary():
    L = axes("E")
    L.append(rf"\fill[fsBodyFill] {tp('E', np.vstack([FE, UP[1:]]))} -- cycle;")
    L.append(rf"\draw[fs hidden] {tp('E', UP)};")
    L.append(rf"\draw[fs heavy, line join=round] {tp('E', FE)};")
    for p in population():
        L.append(rf"\node[fs dot, minimum size=3.0pt] at {pt(*p)} {{}};")
    c = P("E", *CEN)
    for deg in (180, 197, 214, 232, 252, 272):
        d = np.array([np.cos(np.radians(deg)), np.sin(np.radians(deg))])
        r0 = 1.0 / np.hypot(d[0] / (RX + 4), d[1] / (RY + 4))   # just outside the population
        a, _ = hit(np.array([P("E", *f) for f in FE]), c, d, closed_=False)
        r1 = min(r0 + 17, a - 4)                                  # and 4 pt short of the front
        assert r1 - r0 >= 13.2, "an arrow too short for its tip"
        L.append(rf"\draw[fs vec] {pt(*(c + r0 * d))} -- {pt(*(c + r1 * d))};")
    for words, at in ((("Pareto", "optimal", "front"), (0.17, 0.21)),
                      (("Feasible", "area", "search"), (0.80, 0.40))):
        L.append(rf"\node[align=center, font=\small] at {pt(*P('E', *at))} {{{BR.join(words)}}};")
    return L


def body():
    L = [r"\begin{tikzpicture}[fs, x=1pt, y=1pt]"]
    L += heading("MULTICRITERIA DECISION MAKING", W / 2, Y_MCDM, rule=(0, W))
    for name, text, lines, ys, yl in (("P", "Priori", PRIORI, Y_SUB1, Y_LIST1),
                                      ("Q", "Posteriori", POSTERIORI, Y_SUB1, Y_LIST1),
                                      ("I", "Interactive", INTERACTIVE, Y_SUB2, Y_LIST2)):
        L += heading(text, LISTX[name] + list_width(lines) / 2, ys)
        L += items(LISTX[name], yl, lines)
    L += priori() + posteriori() + interactive()
    L += heading("EVALUATIONARY ALGORITHMS", W / 2, Y_EA, rule=(0, W))
    L += items(LISTX["E"], Y_LIST3, EVOLUTIONARY)
    L += evolutionary()
    L.append(r"\end{tikzpicture}")
    return "\n".join(L)


if __name__ == "__main__":
    print(body())
