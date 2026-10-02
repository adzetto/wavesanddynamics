# Numerical examples added on 1 October 2026

The waves guide's Figure 4 offers bar, I-beam, rail, pipe and plate. The
plate is infinite across its width and 10 mm thick. Its basis ties nodes at
equal thickness coordinates, separating Lamb and shear-horizontal modes.
The displayed 40 mm width is a slice, not a pair of free edges.

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
Playwright with Chromium. The existing figure runtime supplies the canvas
layout, Computer Modern fonts, pause/restart, reduced motion and print stills.

```powershell
$env:OPENBLAS_NUM_THREADS = '1'
python tools/numfig/dispersion.py --page
python tools/numfig/dispersion_wavelength.py
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
host can challenge with HTTP 429. The sibling JSON files remain reproducible
numerical artifacts; interactive figures use the embedded copies.

## Additional requests checked on 2 October 2026

Figure 4's bar uses 16 × 32 Q9 elements in both the Python sweep and the browser
solver. The I-beam, rail, pipe and plate use 1.5 times their previous mesh
density. Production meshes are compared with finer reference meshes. Large
Python eigenproblems use sparse shift-invert, with independent dense checks.
The browser retains its eigenvalue-counting solver.

The reference paper [Xu et al. (2024)](https://doi.org/10.1038/s41598-024-59328-5)
uses a 192 mm high, 150 mm wide, 75 kg/m rail with 550 triangular elements and
340 nodes. This guide's simplified rail is 40 mm high and 35 mm wide, uses
quadratic quadrilaterals, and retains the guide's steel properties. Matching
the paper's number of branches would require its geometry and material too.
Here each displayed branch is checked against the eigenvalue count of this
guide's own cross-section, rather than adding curves to match a picture.

Figure 4a now shows **wavenumber**, as requested in the latest feedback. Its
existing filename is retained so earlier links keep working. Wavelength
continues to appear in each wave's numerical readout.

Figure 1 offers undamaged, storey-3 and storey-5 damage presets, plus a stiffness
slider for each of its five storeys (20–150% of the baseline). A symmetric
Jacobi eigensolver recomputes mass-normalized modes and frequencies in the
browser. Every comparison keeps the original roof impulse. The spectrum is
the FFT of 32 physical seconds of the exact undamped roof displacement, sampled
at 64 Hz with a Hann window and coherent-gain amplitude correction.

Figure 18's neuron-count selection also draws its fitted 1–N–1 network, with
N hidden tanh units and every input/output connection. Its displayed output
bias is `base + sum(v)` because the existing fit uses `v * (1 + tanh(...))`.
There are `3*N + 1` fitted weights and biases.
