# Numerical examples added on 1 October 2026

The waves guide's Figure 4 offers bar, I-beam, rail, pipe and plate. The
plate is infinite across its width and 10 mm thick. Its basis ties nodes at
equal thickness coordinates, separating Lamb and shear-horizontal modes.
The displayed 40 mm width is a slice, not a pair of free edges.

Figure 4a plots wavelength on a logarithmic vertical axis, in millimetres,
against frequency. It uses Figure 4's same meshes, branches and SAFE solver.
It computes wavelength directly as `2π/k = c_p/f`. It retains the same
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
