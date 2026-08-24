# Changelog

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
  `defect_on_dense_gas_coolprop` (13.8 % on Burro 8 with the CoolProp water
  backend), and the two P-W1 counts.

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
