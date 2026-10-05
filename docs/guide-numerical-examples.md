# Numerical examples added on 1 October 2026

The waves guide's Figure 4 offers bar, I-beam, rail, pipe and plate. The
plate is infinite across its width and 10 mm thick. Its basis ties nodes at
equal thickness coordinates, separating Lamb and shear-horizontal modes.
It is drawn as a thin slab 140 mm wide, a slice of the infinite plate, not a
pair of free edges.

Figure 4a plots wavenumber on a logarithmic vertical axis, in radians per
metre, against frequency. It uses Figure 4's same meshes, branches and SAFE
solver. It computes wavenumber directly as `k = 2πf/c_p`. It retains the same
phase-velocity window so the two figures compare the same branches.

The machine-learning guide has two additional figures:

- Figure 3a: seasonal ARIMA, additive Holt-Winters smoothing and recursive
  gradient boosted trees forecast the same synthetic monthly sensor signal.
  Three forecast origins each have a 24-month horizon. Future observations
  do not enter training or recursive lag features. RMSE and MAE are measured
  on the withheld observations. Only ARIMA displays a prediction interval.
- Figure 6a: correlation filtering, forward selection with cross-validation
  and a Lasso coefficient path on the same synthetic six-feature regression.
  Selection uses 360 training rows; 120 held-out rows evaluate the resulting
  subsets with the same Ridge predictor. Cross-validation fits its scaler
  inside each fold. The fixed Lasso penalty is 0.12.

The examples use deterministic simulated data, not measured experimental
data. Their results describe these examples; they do not establish a general
ranking of the methods.

## Regenerate

Python dependencies: numpy, scipy, scikit-learn, statsmodels, Pillow and
Playwright with Chromium; `triangle` only to mesh the I-beam and the rail
again. The existing figure runtime supplies the canvas
layout, Computer Modern fonts, pause/restart, reduced motion and print stills.

```powershell
$env:OPENBLAS_NUM_THREADS = '1'
python tools/numfig/dispersion.py --page
python tools/numfig/dispersion_wavelength.py
python tools/numfig/safe.py
python tools/numfig/ml_feature_selection.py
python tools/numfig/ml_forecasting.py
python site/build.py --strict --no-word --out build/r14-guides/dist
python -m pytest tests/test_anim_figures.py tests/test_guide_supplements.py tests/test_site.py -q
```

The full `dispersion.py` run also refreshes its original still and complete
validation report. `dispersion_plate.check.txt` records the new independent
plate checks and the browser solver against SciPy for all five sections.

`content/anim/anim.supplements.json` registers the additional animation assets.
`content/anim/supplements.json` sets their captions and placement anchors.
The build requires each anchor to match once and a printed frame to exist.
The Word source and the original figure numbers remain intact. Added figures
use lettered numbers and share the site's full-screen, no-script and print
fallbacks.

## Validation

The plate's A0/S0 phase velocities were checked against the independent
Rayleigh-Lamb equations, S0 against the plate extension limit and SH0 against
the exact shear speed. The JavaScript eigenpairs and group velocities were
checked against SciPy across every section. Each generator checks its printed
frame and intro for colliding labels and strokes.

The feature-selection generator checks Pearson correlation against a
standardized dot product and the true regression coefficients against least
squares. The forecasting generator changes every future observation by 500
and refits: all three forecasts must remain unchanged.
# Production data loading

Both dispersion figures embed all five section payloads in their HTML. Section
selection therefore works without separate JSON requests, which the production
host can challenge with HTTP 429. No separate JSON files are written or read.

## Additional requests checked on 2 October 2026

Large Python eigenproblems use sparse shift-invert, with independent dense
checks. The browser retains its eigenvalue-counting solver.

Figure 4a now shows **wavenumber**, as requested in the latest feedback. Its
existing filename is retained so earlier links keep working. Wavelength
continues to appear in each wave's numerical readout.

Figure 1 offers undamaged, storey-3 and storey-5 damage presets, plus a stiffness
slider for each of its five storeys (20–150% of the baseline). A symmetric
Jacobi eigensolver recomputes mass-normalized modes and frequencies in the
browser. Every comparison keeps the original roof impulse. The spectrum is
the FFT of 32 physical seconds of the exact undamped roof displacement, sampled
at 64 Hz with a Hann window and coherent-gain amplitude correction.

Figure 18b's neuron-count selection also draws its fitted 1–N–1 network, with
N hidden tanh units and every input/output connection. Its displayed output
bias is `base + sum(v)` because the existing fit uses `v * (1 + tanh(...))`.
There are `3*N + 1` fitted weights and biases.

## Figures 4, 4a and 5 rebuilt on 5 October 2026

The professor's notes asked for as many dispersion curves as the papers show,
checked mesh sizes, wave speeds that make the change along a curve visible,
and the plate drawn as a thin slab. Each section now has real dimensions and
its own frequency window, ending where it holds as many branches as its
reference:

| Section | Window | Branches | Reference |
|---|---|---|---|
| Square bar 20 × 20 mm | 0 to 190 kHz | 11 | Hayashi, Kawashima and Rose (2004), Fig. 2 |
| IPE 80 I-beam | 0 to 52 kHz | 20 | none published; the same model on a mesh of half the element size |
| 60E1 rail (EN 13674-1) | 0 to 22.5 kHz | 16 | Ramatlo, Wilke and Loveday (2018), Fig. 1(a) |
| NPS 1¼ schedule 40 pipe | 0 to 175 kHz | 22 | exact (Gazis 1959) |
| Plate, 10 mm | 0 to 250 kHz | 5 | exact Rayleigh-Lamb and SH |

Every mesh is compared with one of half its element size: cut-on frequencies
agree within 0.17% and curve ends within 0.16%, with 6 to 12 elements across
the shortest wavelength shown. The bar has 16 × 16 Q9 elements of 1.25 mm, and
Figure 5's SAFE panel uses the same mesh. Each section runs on one clock,
labelled in its parameter line; on screen, packets move at the group velocity
and crests at the phase velocity. `dispersion_branches.check.txt` holds the
branch audit, and `dispersion.check.txt` the full report.
