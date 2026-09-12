# Changelog

## 0.1.5 — 2026-09-12

- Add validated, JSON-serialisable `SourceLedger`/`SourceState` input handoff.
- Reject unresolved liquid accumulation in the ledger-to-pool adapter.

## 0.1.3 — unreleased candidate

### Additional verification on 2026-08-29

- Regenerated the six Pasquill-class critical-wind fits from the evaluated
  width-coupled configuration and corrected the frozen coefficients.  The
  checked class-D curve is now `2.611924 q^0.133865`.
- Added `scripts/fit_critical_wind.py` as a public, model-only reproducer.  In
  the measurement-free release it recomputes the fit in memory before checking
  the frozen constants.
- Added a manuscript-only same-test SLAB/FLACS comparison.  Its script embeds
  transcribed measurement and published FLACS values, so the release builder
  now enforces that it remains in the private archive.
- Tightened the public builder: the generated README is scanned, JSON/CFF/YAML
  are included in the value scan, and private results, build artefacts and
  caches are rejected structurally.
- Updated the package metadata to the SPDX license expression and explicit
  license-file form required by current setuptools, removing the deprecated
  TOML license table before release.
- Added an sdist manifest so the PyPI source archive carries the public
  reproducibility scripts, documentation, filtered catalogue and provenance
  guide as well as the importable package. Private comparison and manuscript
  scripts remain explicitly excluded.
- Replaced the stale rounded and intermediate critical-wind values in the
  public README, premise note and results register with the regenerated 0.1.3
  coefficients and current FFI/NASA premise ratios.
- Revised the manuscript to introduce the implementation package only after
  the SLAB formulation, and expanded the derivation and limitations of the
  post-run applicability diagnostic and pre-run screening curve.

### Corrected after the release audit

- `water_ice` now tests the water pressure curve and fusion enthalpy
  independently. This fixes the slabx 1.0.5 compatibility case, where pressure
  was corrected but 333.4 kJ/kg of fusion enthalpy was still missing, while
  preserving the no-double-add guard on slabx 1.0.6.
- The LNG negative control now toggles only the hydrogen-specific width gate
  with identical water treatment on both arms. All ten cases are bit-identical
  (0.0 %). The non-zero water result is now a separate
  `cross_fluid_water_effect` ablation (maximum 13.417 %; Burro 8 13.54 %), with
  no pass/fail label and no claim that slabx 1.0.6 remains defective.
- The humidity conclusion is split into the claim the sweep supports and the
  stronger claim it falsifies. Both horizontal trials are under-predicted at
  every RH tested, but strict orientation separation fails at RH 100 % and the
  bracket count changes from three to five of six.
- The 30 m sensor array is a polar arc, not a fixed downwind cross-section.
  After rotation into the wind frame, its downwind coordinate spans
  18.88--29.84 m in Test 4 and 10.26--29.97 m in Test 6. The previously
  reported 0.34--0.41 lateral mean/peak ratio is withdrawn because it also
  divided temporal means by temporal maxima.
- The entrainment figures 2.076/2.479 and 4.547/5.560 remain available only as
  conditional scenarios. The half-peak case is illustrative rather than a
  verified Gaussian profile; peak-equals-bulk maximizes the inferred ratio and
  is not a lower bound.
- Frozen paper results now require measured data, five bracket matches, the
  1.1138 required factor, a separate width-gate negative control, and a
  separate cross-fluid water result. New regression tests pin each distinction.

This patch release changes interpretation and release artefacts, not the core
SLAB integration equations. It requires a new version-specific archive DOI;
the concept DOI remains `10.5281/zenodo.22075011`.

## 0.1.2 — 2026-08-24

### Added

- `scripts/humidity_sensitivity.py` — six FFI trials at six humidities.
  **The bracket count depends on the assumed humidity**: five of six above
  75 %, three of six below 50 %. The orientation split does not: the two
  horizontal trials stay at 0.29 to 0.40 across the whole range.
- `scripts/sensor_audit.py` — what the arc sensors do and do not resolve.
  Its original 0.34 to 0.41 lateral mean/peak interpretation is **withdrawn in
  0.1.3**: a polar arc is not a fixed-x cross-section, and the calculation
  mixed temporal means with temporal maxima.
- `scripts/entrainment_uncertainty.py` — two explicit scenarios rather than a
  span.
- `scripts/ffi_summary_table.py` — one table for all six trials.
- `benchmark_runtime.py --batch35 --parallel` — the full 35-scenario set.
- `results.json` now carries `definitions`, `provenance`,
  `humidity_sensitivity`, and the real `slabx_version` from distribution
  metadata rather than `unknown`.


### Withdrawn

- **`Trajectory.R_flux` is a half-plume flux**, and three derived numbers read
  it as the total. `2 * R_flux[0]` equals the release rate to twelve figures
  on every FFI trial; `TestRFluxIsAHalfFlux` now pins it.

  Withdrawn: the near-field entrainment excess of 2.6 (a multiplication using
  `R_flux[0]` as the release rate), the corrected 1.72 (a half flux), the
  vertical-displacement factor of 1.65 (a difference of two ratios, one of
  them from a half flux), and the 0.8 to 5.9 span (five assumptions treated
  as independent when two cancel and two are the same knob).

  **Replaced by two explicit scenarios.** Test 6 at 30 m: the model's total
  flux is 254.630 kg/s, against 102.706 inferred if the arc reading is a
  Gaussian centreline value (**2.479**) and 45.793 if it is already the
  cross-sectional mean (**5.560**). Test 4 gives 2.076 and 4.547.

- **"Three symptoms, one number" is withdrawn.** Near-field mixing and the
  downstream lift-off timing are separate phenomena, and no single
  entrainment correction has been shown to address both.


### Fixed — found by a full audit

- **`plume_width` and `depth_cap` silently disabled each other.** Both rebind
  `plume.entrainment`, so installing one over the other replaced it: a run
  with both enabled returned exactly the second module's answer, with no
  error and no warning, and which module survived depended on the order. On
  NASA test 6 the pair gave 388.94 or 599.52 m against 242.31 m when both
  actually run. Both now chain onto whatever is already installed.

  **Third occurrence of this failure mode**, after bug 8 and the depth-cap
  frame walk. `TestPatchesCompose` pins order-independence and mutual
  non-erasure.

- **`test_the_same_thread_may_nest` asserted nothing.** It ran the nesting
  and proved only that no exception was raised.

### Changed

- **Grid independence was overstated.** The documents claimed 0.1 % across
  `x_max` from 120 to 1200 m, measured on one trial. Across all six it is
  **0.07 to 1.65 %**, the largest on the trial that lofts. `n_puff_steps`
  still has no effect in plume mode.

**No published result changed.** The water defect, the LFL bracket count, the
required factor, the pool radii, the P-W1 counts, the residual errors, the
critical-wind coefficients and the E3.5 correlations are all identical.


### Fixed

- **The 2x2 ablation collapsed on slabx 1.0.6.** Its "correction off" arm used
  an unwrapped water backend, and 1.0.6 carries the correction upstream, so
  every `W0` cell equalled its `W1` neighbour. The design reported that the
  water correction changes nothing -- **a null result it never tested**.
  `slabx_lh2.water_ice.clamped` now reproduces the pre-1.0.5 behaviour
  deliberately, so the comparison means the same thing on any version.
  `TestTheAblationActuallySeparates` fails if it collapses again.

- The pool-radius median printed by `reproduce.py` took the upper of the two
  middle values on an even-sized set, so the printed 1.11 disagreed with the
  1.03 in `results.json`.

- A test probed for the measured datasets separately from the script that
  used them; where the package and the scripts lived in different places the
  two disagreed and the test failed instead of skipping. It now reads the
  flag `reproduce.py` records.

## 0.1.1 — 2026-08-24

Corrections found by an independent review of the 0.1.0 release. **No new
physics; every model equation is unchanged.**

### Fixed

- **`scripts/reproduce.py` failed on a public install.** Without the measured
  arc concentrations it raised `TypeError: 'NoneType' object is not iterable`.
  `collect()` handled the missing brackets and the printed sections did not,
  so the documented behaviour — reproduce every model output, skip only the
  comparisons against measurement — was not what happened. Now completes and
  marks the missing brackets. Pinned by
  `test_reproduce_completes_without_the_measurements`.

- **`results.json` was missing three results the documents quote.**
  the former `defect_on_dense_gas_coolprop` result (now replaced by an
  explicitly deliberate cross-fluid ablation), and the two P-W1 counts.

- **The residual check compared mismatched configurations.** The scaling
  decomposition is measured with the width coupling active, and the predicted
  exponent was being compared against the run that also had the exploratory
  drag. Corrected, the four errors are 3.0, 3.1, 5.7 and 5.9 %.

### Withdrawn

- **The comparison against "PHMSA's factor of 2.5" is wrong and is removed.**
  49 CFR 193.2059(b)(1) sets an *average gas concentration in air of 2.5
  percent* — a dispersion endpoint, not a distance multiplier. The two have
  different dimensions. There is no regulatory distance factor to compare
  `SAFETY_FACTOR` against.

### Changed

- **P-W1 is reported as two numbers**, because they differ and the
  distinction matters: `0/4` with the registered width coupling alone, `1/4`
  with the exploratory vertical drag added. **Neither is recorded as a pass** —
  the outcome is dominated by the pool radius, which the NASA paper does not
  report.

- **Upstream status.** The documents said the clamp was still present in
  slabx; it was corrected upstream in **1.0.5** (saturation pressure) and
  **1.0.6** (fusion enthalpy). The `slabx` column of the feature tables refers
  to **1.0.4 and earlier**.

- Claims of the form "no other model does X" are now "we found no X in the
  documentation we reviewed", and the model tables distinguish **not found**
  from **not verified**.

- `docs/39` carries a reference list. Three entries could not be checked
  against the original report numbering and say so.

## 0.1.0 — 2026-08-24

First release.
