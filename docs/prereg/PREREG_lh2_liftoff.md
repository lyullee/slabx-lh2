# Pre-registration: lift-off and ground reflection for a detached buoyant cloud

**Registered 2026-08-21, before the branch was written and before any
comparison was run.** Nothing above the `RESULTS` line is to be edited
afterwards.

Supersedes `PREREG_lh2_buoyant_rise.md`; see
`WITHDRAWN_PREREG_lh2_buoyant_rise.md` for why that registration was
withdrawn.

---

## The claim under test

The plume core already carries buoyant rise: for `rho <= rho_a` it recovers
`w_c` from the EQ 6a integral and `z_c` climbs. On FFI Test 4 it reaches
2.5 m by the 100 m arc, against a measured concentration maximum at 1.8 m —
the highest sensor available.

The post-processing then hides it. `post/concentration.py` builds the
vertical profile as a **reflected** Gaussian about `z_c` with
`sigma_z = (h - z_c)/sqrt3`. At the 100 m arc `sigma_z` is 5.5 m against
`z_c` of 2.3 m, so the image term is nearly as large as the direct term at
the ground:

| z [m] | direct | image | sum |
|---|---|---|---|
| 0.1 | 0.952 | 0.940 | 1.892 |
| 1.8 | 0.999 | 0.804 | 1.803 |

**While full reflection is applied and `sigma_z` exceeds `z_c`, the predicted
maximum sits at the ground at every rise height.** The measurement at 100 m
increases with height (0.6, 0.7, 0.8 %vol at 0.1, 1.0, 1.8 m), which a fully
reflected profile cannot produce.

Reflection is correct for a cloud in contact with the ground. It is wrong for
one that has lifted off. SLAB has no criterion that distinguishes the two,
because SLAB's clouds do not lift off.

## What is being added

**A single criterion, taken as published.** Hall & Walker (2000), reported in
AEAT/NOIL/27328006/001 (URAHFREP WP7):

    onset of rise    F / (W u^3)  ~ 0.01
    lift-off         F / (W u^3)  ~ 0.035    (ground concentration falls to
                                              10-20 % of the maximum)

`F` is the buoyancy flux, `W` the source width, `u` the wind speed at the
reference height. Between the two thresholds the reflection coefficient is
interpolated linearly from 1 (fully grounded) to 0 (fully detached); outside
them it is clamped. The thresholds and the endpoints are the measured ones.

**Free parameters: zero.** The interpolation between two measured thresholds
is a choice of form, not of value, and the linear form is the one that makes
the endpoints the measurement. No coefficient is available to adjust.

The trajectory is untouched: `w_c`, `z_c` and `h` are not changed. Only the
reflection term in `post/concentration.py` is.

## Predictions

| # | Prediction | Criterion |
|---|---|---|
| **P-L1** | The concentration maximum leaves the ground where the criterion says it does | on Test 4 the predicted maximum sits **above z = 1.0 m at the 100 m arc**; it currently sits at the lowest sensor at every arc |
| **P-L2** | The near field is untouched, because the criterion is not met there | Test 4 at **30 m changes by < 5 %**, where the measurement puts the maximum at the ground (17.2 / 16.7 / 11.8 %vol at 0.1 / 1.0 / 1.8 m) |
| **P-L3** | The reflection coefficient reaches the measured lift-off value where the flux does | at F/(Wu³) = 0.035 the ground concentration is **10 - 20 %** of the maximum, on the Hall & Walker source series |
| **P-L4** | The vertical ordering flips at the arc where the measurement flips | predicted concentration **decreasing** with z at 30 m and **increasing** with z at 100 m, matching the sign of the measured gradient at both |
| **NC1** | A dense cloud never meets the criterion | the ten LNG pool trials are **bit-identical** |
| **NC2** | A neutral cloud with no buoyancy flux is unchanged | Prairie Grass concentrations and widths **bit-identical** |

P-L4 is the discriminating one. P-L1 could be satisfied by any change that
enlarges the plume height; P-L4 requires the change to act at the right arc
and in the right direction at both ends.

## What would falsify

If **P-L2 fails** — if the near field moves — the criterion is firing where
the cloud is demonstrably grounded, and the implementation is wrong rather
than the physics.

If **P-L1 passes and P-L4 fails**, the maximum has been moved but not by the
mechanism claimed, and the branch is not adopted.

If **NC1 or NC2 fails**, the change has leaked into the dense and passive
limits that this project's existing validation rests on, and it is a defect
regardless of what it does for LH2.

## What must not happen

**The added-mass term is not to be reintroduced.** `PREREG_added_mass` found
the oblate-spheroid `B/h` shape function to be the wrong shape function
rather than a mis-scaled one — the width spread saturates at 1.46 and
tripling `C_A` does not improve it. `c_added_mass` stays at 0 and is not
swept.

**`sigma_z` is not to be adjusted.** The obvious alternative fix is to shrink
the cloud depth until the profile peaks off the ground. That is a coefficient
fitted to the quantity it is meant to predict. If the reflection criterion
fails, the depth hypothesis is registered separately as
`PREREG_lh2_depth.md` with its own independent target — it is not to be
tried inside this test.

**An improved aggregate is not a result.** `PREREG_froude` rejected the
Robins closure although it was better than the original on every aggregate
measure, because the mechanism it was introduced to fix was not fixed. If
P-L2 and P-L4 do not both pass, this branch is not adopted however good
FAC2, MG or VG become.

## Scope

Four unignited FFI trials, three arcs, three heights. **n = 4.** Document 07
§7.3 puts the detectable MG ratio at this sample size near 1.6, so aggregate
statistics from this test are graded **C**. P-L2, P-L4, NC1 and NC2 are
deterministic and are not subject to that limit.

FFI Test 2 is excluded: the wind was from 82 degrees, the array was moved,
and the radii are 9.01, 11.04 and 30 m rather than the 30/50/100 m grid.

The default stays as Ermak wrote it. Lift-off is a variant, off unless asked
for.

---

## RESULTS

*(appended 2026-08-21 after the run; nothing above this line was edited)*

### Negative controls, run first

| | max F/(Wu³) | bit-identical | max abs difference |
|---|---|---|---|
| **NC1** LNG pool (Burro 8 deck) | **0.0762** | **no** | 3.93e-4 (volume fraction) |
| **NC2** passive SO₂ ground release | 0.000000 | **yes** | 0.000e+00 |

**NC2 — PASSED.** The buoyancy deficit is clamped at zero for a cloud denser
than air, so the criterion returns exactly zero and the reflection is
untouched. Bit-identical.

**NC1 — FAILED.** The criterion fires on a dense-gas trial. Diagnosed: it
fires on rows 52-57 of 58, at **x = 4.4 to 8.5 km**, where

| x [m] | F/(Wu³) | rho/rho_a | B [m] |
|---|---|---|---|
| 4364 | 0.0121 | 1.00000 | 301 |
| 8541 | 0.0762 | 1.00000 | 347 |

At that range the density ratio is 1.00000 to five figures — the deficit is
at the rounding floor — while `u` is 1.94 m/s so `1/u^3` is large and the
volumetric flux has grown by three orders of magnitude. **The group is being
evaluated on numerical noise.** Within the range the trial is used for (the
LFL distance is 449 m) nothing changes at all; the first firing is at ten
times that distance.

The registered criterion was bit-identity and it is not met. **NC1 is
recorded as failed.** The registration states that a negative-control failure
makes the branch a defect regardless of what it does for LH2, and that
stands.

### P-L1 — FAILED

The reflection coefficient is **1.000 at every arc of every trial**. Nothing
moves. The height of the maximum stays at 0.00 m at both 30 m and 100 m.

Maximum F/(Wu³) at the arcs (x >= 25 m), against an onset threshold of 0.01:

| | Test 1 | Test 3 | Test 4 | Test 7 |
|---|---|---|---|---|
| max F/(Wu³) | 0.00411 | 0.00487 | 0.00480 | 0.00317 |

**Two to three times below onset everywhere the sensors are.**

### P-L2 — PASSED, vacuously

Test 4 at 30 m changes by 0.000 %, against a criterion of < 5 %. It passes
because nothing fired anywhere, not because the criterion is confined to the
far field. **This is not evidence for the mechanism** and must not be
reported as though it were.

### P-L3 — FAILED, and independently of the criterion

At full detachment (`r` = 0) the ground-to-maximum ratio is
`exp(-z_c^2 / 2 sigma^2)`, a property of the profile alone. On Test 4:

| x [m] | z_c [m] | sigma_z [m] | z_c/sigma | ground/max at r = 0 |
|---|---|---|---|---|
| 31.8 | 0.51 | 3.10 | 0.166 | **0.986** |
| 52.1 | 0.70 | 4.04 | 0.174 | 0.985 |
| 96.6 | 1.73 | 5.25 | 0.330 | 0.947 |
| 140.0 | 2.98 | 6.02 | 0.496 | **0.884** |

The measured lift-off signature is a ground concentration of **10 - 20 %** of
the maximum. Reaching it needs `z_c/sigma` of about **1.8 - 2.1**. The model
reaches **0.50** at the far end of the domain.

**So even with the reflection removed entirely, the profile cannot show
lift-off.** The reflection was never the binding constraint.

### P-L4 — FAILED

Test 4, concentration at three heights [%vol], reflection off and on:

| arc | r | off: 0.1 / 1.0 / 1.8 | gradient | on: 0.1 / 1.0 / 1.8 | gradient | **measured** |
|---|---|---|---|---|---|---|
| 30 | 1.000 | 6.009 / 5.715 / 5.102 | down | 6.009 / 5.715 / 5.102 | down | **down** ✅ |
| 50 | 1.000 | 3.182 / 3.090 / 2.891 | down | 3.182 / 3.090 / 2.891 | down | **up** ❌ |
| 100 | 1.000 | 1.358 / 1.336 / 1.289 | down | 1.358 / 1.336 / 1.289 | down | **up** ❌ |

The sign of the vertical gradient matches at 30 m and is wrong at 50 and
100 m, exactly as before the branch was added.

### Status

| | |
|---|---|
| NC1 | **FAIL** — fires on a dense trial at x > 4.4 km |
| NC2 | **PASS** — bit-identical |
| P-L1 | **FAIL** — criterion never reached; maximum stays at the ground |
| P-L2 | **PASS (vacuous)** — nothing fired, so nothing moved |
| P-L3 | **FAIL** — ground/max 0.88-0.99 against a measured 0.10-0.20 |
| P-L4 | **FAIL** — vertical gradient unchanged at 50 and 100 m |
| **adoption** | **REJECTED** |

### What this establishes

**The dimensionless group does not discriminate.** Mapped onto a dispersing
cloud it returns 0.003 - 0.005 where the measurement says the cloud has
lifted, and 0.076 on a dense LNG cloud that never leaves the ground. It is
below threshold where lift-off happened and above threshold where it did not.

That is the same shape as `PREREG_added_mass` P-AM7: **the variable is wrong,
not its coefficient.** Hall & Walker's `F/(W u^3)` characterises a
*ground-level area source of fixed width releasing a fixed buoyancy flux*.
A dispersing cloud has a width that grows and a buoyancy flux that is spread
over it, and the group inherits neither meaning. The module docstring flagged
this mapping as the weak point before the run; the run confirms it.

**And P-L3 settles something the test was not aimed at.** With reflection
removed entirely the profile still cannot produce the measured signature,
because `sigma_z = (h - z_c)/sqrt3` is three to six times `z_c` across the
whole domain. Whatever governs the vertical structure of a lifted LH2 cloud,
**it is the cloud depth and not the ground reflection.** The reflection
hypothesis is eliminated, which is what a negative result is for.

`PREREG_lh2_depth.md` follows. It must carry an independent target for the
depth — fitting `sigma_z` to the profile it is meant to predict is what
§"What must not happen" above forbids, and that prohibition is not weakened
by this failure.

### Reproduction

```bash
cd lh2mod
python3 diag_flux.py      # F/(Wu^3) along the trajectory, four trials
python3 run_prereg.py     # negative controls and P-L1, P-L2, P-L4
python3 addendum.py       # P-L3 and the NC1 diagnosis
```

