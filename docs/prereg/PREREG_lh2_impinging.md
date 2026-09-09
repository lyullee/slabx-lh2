# Pre-registration: a source model for a downward impinging cryogenic jet

**Registered 2026-08-21, before the class was written and before the
dispersion comparison was run.** Nothing above the `RESULTS` line is to be
edited afterwards.

All runs use the corrected water saturation of document 23 (IAPWS sublimation
below the triple point), on both arms of every comparison.

---

## The gap

SLAB has four source types: evaporating pool, horizontal jet, vertical
(upward) jet, instantaneous. **A cryogenic two-phase jet directed downward
onto the ground is none of them.**

Document 18 §18.4 measured what that costs. FFI Tests 3 and 4 differ in
tanker pressure by nothing, in nozzle by nothing, in release rate by 1.13x —
and in orientation:

| | Test 3 | Test 4 |
|---|---|---|
| orientation | **vertical down** | **horizontal** |
| release rate | 0.730 kg/s | 0.828 kg/s |
| measured maximum at 30 m, z = 1 m | 6.2 %vol | **16.7 %vol** |
| ratio | | **2.69** |
| `slabx`, both run as `HorizontalJet` | 6.05 | 6.04 |
| ratio | | **1.03** |

Document 18 §18.8.1 then showed no coefficient closes it: across thirty
settings of six coefficients, spanning `alpha_g` from 0 to 1.0, the ratio
stays between 0.996 and 1.006. **Orientation is not a state variable, so no
function of the state can carry it.**

Document 23 §23.5 finds the same signature on E3.5, where the residual
changes sign with nozzle size — 12 mm over-predicted, 25.4 mm under-predicted.

## The mechanism

RR986 states it directly for its own test 6: the release was directed
vertically downward at 100 mm **"to provide a release configuration where the
momentum of the jet was removed on contact with the ground"**.

So a downward jet is not a jet by the time it disperses. It delivers liquid to
the ground and becomes a pool. A horizontal jet keeps its momentum and stays a
jet. Running both through `HorizontalJet` erases the distinction.

RR986 also states the pool reaches a steady size: **"once the pool was
established the extent of the pool remained constant throughout the release.
This could be an equilibrium effect at this flow rate."**

That equilibrium is a mass balance. The pool grows until the area it covers
evaporates as fast as liquid arrives:

    pi R^2 E = q (1 - x)        =>      R = sqrt( q (1-x) / (pi E) )

`x` is the post-flash vapour fraction, from an isenthalpic flash to
atmospheric pressure through CoolProp. `E` is the evaporative mass flux, taken
as the late-phase regression rate of about 1 mm/s that PRESLHY E3.4
(Friedrich 2023), Takeno et al. (1994), Bailey et al. (1960) and ISO TR
15916:2015 Annex B.1 all report — so `E` = rho_L x 1e-3 = 0.0708 kg/(m2 s).
The late-phase value is the right one because the quantity being predicted is
the steady radius, which is what RR986 observed.

**Free parameters: zero.**

## Calibration, already performed

Against reported pool radii, which are lengths and not concentrations:

| case | R predicted [m] | R observed [m] | pred/obs |
|---|---|---|---|
| E3.5 trial 7 (12 mm, 1 bar) | 0.67 | 0.70 | **0.95** |
| E3.5 trial 13 (12 mm, 5 bar) | 0.95 | 1.20 | 0.80 |
| RR986 test 6 (60 L/min) | 0.55 | 0.83 | 0.66 |
| FFI Test 1 (2 barg) | 0.95 | 0.75 | 1.26 |
| FFI Test 7 (0.8 barg) | 0.83 | 0.75 | 1.11 |
| FFI Test 3 (10 barg) | 1.35 | 0.75 | 1.81 |
| NASA Test 6 | 6.51 | 2.50 | 2.60 |

Median 1.11; excluding NASA, whose pool was confined by the 9.1 m pond's
0.6 m clay walls, 0.66 to 1.81.

**This is the calibration and it is complete. Nothing below is fitted, and the
radii above are not used again.**

## The intervention

A fifth source class. Given orientation, release height, nozzle area, rate and
tanker pressure:

1. isenthalpic flash to 1 atm through CoolProp gives `x`
2. liquid delivered to ground `m_liq = q (1 - x)`
3. equilibrium radius `R = sqrt(m_liq / (pi E))`
4. the source is an evaporating pool of area `pi R^2` at the full rate `q`
5. **the jet's momentum is discarded**, which is the physical content

Existing source classes are untouched.

## Predictions

| # | Prediction | Criterion |
|---|---|---|
| **P-I1** | The orientation difference appears | FFI Test 4 / Test 3 concentration ratio at 30 m, z = 1 m, reaches **2.0 or more**; measured 2.69, currently 1.03 |
| **P-I2** | It comes from Test 3 falling, not Test 4 rising | Test 4 changes by **less than 1 %** — it is horizontal and does not touch the new class |
| **P-I3** | The same distinction appears on the other vertical-down trials | FFI Tests 1 and 7 concentrations at 30 m **fall**, and by less than Test 3 does, since their rates are lower |
| **P-I4** | E3.5's nozzle-dependent residual is reduced | on the three E3.5 vertical-down trials (7, 8, 13) the vertical ratio at 10 m moves **toward** the measured value |
| **NC1** | The dense set is untouched | ten LNG pool trials **bit-identical** — none is a downward jet |
| **NC2** | Horizontal LH2 is untouched | FFI Test 4 and the ten horizontal E3.5 trials **bit-identical** |

**P-I1 with P-I2 is the discriminating pair.** A change that raised Test 4
would close the ratio without the mechanism. The mechanism says Test 3 falls
and Test 4 does not move at all.

## What would falsify

**P-I1 above 4.0**: over-corrected. A downward jet that disperses less than
half as far as measured is not an improvement on one that disperses too much.

**P-I2 failing**: the class has reached a horizontal release, which it must
not.

**P-I1 passing while P-I3 fails**: the effect is specific to one pair rather
than to orientation, and the mechanism claimed is not the one acting.

**Either negative control failing**: the class has leaked.

## What must not happen

**`E` is not to be swept.** It is 0.0708 kg/(m2 s) from four independent
measurement series. The calibration above is closed; if the dispersion
comparison fails, `E` is not the thing to adjust, because it was set against
radii and adjusting it to concentrations would destroy the independence that
makes the calibration worth anything.

**The pool radii above are not to be revisited.** They are the calibration.

**An improved aggregate is not a result.** `PREREG_froude` rejected the Robins
closure although it was better on every aggregate measure, because the
mechanism it was introduced to fix was not fixed. If P-I1 and P-I2 do not both
pass, this is not adopted.

## Scope

The discriminating comparison rests on **one pair of trials**. FFI Tests 3 and
4 are the only pair in any available dataset that differ in orientation at
matched rate, pressure and nozzle. **Grade C** for the magnitude; P-I2, NC1
and NC2 are deterministic.

The default stays as Ermak wrote it: four source types. The fifth is a
variant, used only when asked for.

---

## RESULTS

*(appended 2026-08-21 after the run; nothing above this line was edited)*

### Negative controls, run first

| | |
|---|---|
| **NC1** LNG pool trials | **PASS** — bit-identical; no trial in the dense set is a downward jet, so the class is never reached |
| **NC2** FFI Test 4, horizontal | **PASS** — 6.3835 -> 6.3835 %vol, change **0.0000 %** |

### The intervention, and what it did

| test | orientation | `x_vap` | pool R [m] | off [%vol] | on [%vol] | change |
|---|---|---|---|---|---|---|
| 1 | down | 0.112 | 0.95 | 0.1338 | **0.0000** | −100 % |
| 3 | down | 0.441 | 1.35 | 6.0850 | **0.0005** | −100 % |
| 4 | horizontal | — | — | 6.3835 | 6.3835 | 0.0 % |
| 7 | down | 0.051 | 0.83 | 2.5875 | 0.7796 | −69.9 % |

### P-I1 — FAILED, over-corrected

Test 4 / Test 3 goes from **1.049** to **13,684**, against a criterion of 2.0
and a measured 2.69. The registration names 4.0 as the point above which the
result is an over-correction rather than an improvement, and this is three
orders past it.

### P-I2 — PASSED

Test 4 moves by 0.0000 %. The class does not reach a horizontal release.

### P-I3 — FAILED

The prediction was that Tests 1 and 7 fall by **less** than Test 3, their
rates being lower. Test 1 falls by 100 %, the same as Test 3. Only Test 7
behaves as predicted (−69.9 %).

### Status

| | |
|---|---|
| NC1, NC2 | **PASS** |
| P-I2 | **PASS** |
| P-I1, P-I3 | **FAIL** |
| P-I4 | not evaluated — moot |
| adoption | **REJECTED** |

### Diagnosis: the cloud lofts, and it is not the runaway

| test | pool R [m] | max `w_c/u` | `z_c` at 30 m [m] | `h` [m] | rho/rho_a at 5 m |
|---|---|---|---|---|---|
| 3 | 1.35 | **0.324** | **6.95** | 4.68 | **0.914** |
| 1 | 0.95 | **0.609** | **13.25** | 4.13 | 0.944 |
| 7 | 0.83 | 0.164 | 2.92 | 5.02 | 0.948 |

`max w_c/u` stays between 0.16 and 0.61, **inside the bent-over premise of
document 22**. This is not the unbounded rise: it is an ordinary lofted plume,
and the 1 m sensor simply ends up far below its centre.

The cause is the source. Delivering the whole release through a low-momentum
pool of 1.35 m radius makes the cloud far more buoyant near the source —
`rho/rho_a` is 0.914 at 5 m, against a jet source that stays near 1.0 — so it
lifts. **The measurement says the real cloud did not: 6.2 %vol at 1 m at
30 m.**

Enabling the plume-width coupling of `PREREG_lh2_plume_width` recovers a
factor of 59 on Test 3 (0.0005 to 0.0294 %vol) and is still four orders below
the measurement. It is not the missing piece.

### What this establishes

**The distinction is real and the implementation removed too much.**

RR986 says the jet's momentum is removed on contact with the ground, and that
is true of the *downward* momentum. What it does not say, and what this run
assumed, is that the momentum vanishes. An impinging jet turns into a **radial
wall jet**: the liquid pools, but the vapour leaves the impact point moving
outward along the ground. That radial momentum is what holds the cloud down
and dilutes it laterally, and modelling the release as a momentumless pool
throws it away.

So the source term for a downward jet is neither `HorizontalJet` (which keeps
the wrong momentum, in the wrong direction, and gives ratio 1.03) nor
`EvaporatingPool` (which keeps none, and gives 13,684). **The measured 2.69
sits between two treatments that bracket it by four orders of magnitude**,
which is a sharper statement of the gap than document 18 §18.4 could make.

### What the successor must add

A wall-jet stage between impact and dispersion: the radial momentum flux is
the vertical momentum flux at impact, `m_dot * v_impact`, redirected into the
horizontal plane, and it decays over the classical wall-jet length scale. The
pool radius calibration of this registration stands and is not revisited —
what changes is that the vapour leaves the pool with momentum rather than
without.

That is a different hypothesis from this one and needs its own registration.
The calibration above is reusable; the dispersion prediction is not.

### Reproduction

```bash
cd lh2mod
python3 pool_radius.py    # the calibration
python3 run_imp.py        # the registered predictions
```


---

## ADDENDUM — the target trial was the wrong one

*(appended 2026-08-21, after the results above; those are not edited)*

### FFI does not report humidity

The weather tables of FFI-RAPPORT 20/03101 (Tables 2.2 to 2.8) give wind
speed, wind direction, ambient temperature and a qualitative note
("Overcast, rain prior to test"). **There is no relative humidity.** Every FFI
run in this project has used an assumed 90 %.

Document 23 established that humidity governs LH2 cloud buoyancy. Sweeping it
across the four FFI trials, with the corrected water saturation:

| assumed RH | FAC2 | MG | VG | Test 1 @30 m | Test 3 @30 m | Test 4 @30 m |
|---|---|---|---|---|---|---|
| 50 % | 0.83 | 0.963 | 1.28 | 3.949 | 6.162 | 6.331 |
| **60 %** | **0.92** | **1.164** | **1.26** | 2.206 | 6.196 | 6.371 |
| 70 % | 0.75 | 1.631 | 2.39 | 1.020 | 6.198 | 6.398 |
| 80 % | 0.50 | 2.909 | 31 | 0.409 | 6.161 | 6.402 |
| 90 % | 0.42 | 6.451 | 3.1e4 | 0.134 | 6.085 | 6.383 |
| 99 % | 0.42 | 15.589 | 2.2e10 | 0.045 | 5.977 | 6.348 |
| **measured** | | | | **1.80** | **6.20** | **16.70** |

**FAC2 spans 0.42 to 0.92 and VG spans ten orders of magnitude, entirely on an
input that was never measured.**

So the FFI arc statistics cannot evaluate any humidity-sensitive change. That
includes the comparison in document 23 §23.5 between the clamped and corrected
water saturation on this dataset, which was run at 90 % on both arms and is
withdrawn. The correctness argument for the sublimation curve — a factor of
4,136 against IAPWS, and 0.36 % on the dense-gas set — is unaffected, because
it never used FFI.

### What is humidity-independent, and it reframes §18.4

Three of the four trials barely move across the whole sweep:

| trial | orientation | model @30 m | measured | verdict |
|---|---|---|---|---|
| 3 | vertical down | 5.98 - 6.20 | 6.20 | **matches, at any humidity** |
| 7 | vertical down | 2.59 - 2.95 | 2.20 | matches |
| **4** | **horizontal** | **6.33 - 6.40** | **16.70** | **under by 2.6x, at any humidity** |
| 1 | vertical down | 0.045 - 3.95 | 1.80 | unusable |

**Document 18 §18.4 was read backwards.** The ratio of 1.03 against a measured
2.69 is not the model over-predicting the vertical-down trial. It is the model
**under-predicting the horizontal one by 2.6x while getting the vertical-down
one right.**

This registration was therefore aimed at the trial that does not need
correcting. Replacing the vertical-down source made Test 3 worse — it was
already right — which is why P-I1 over-corrected by three orders of magnitude.
The failure is now explained: not that a momentumless pool removes too much
momentum, but that there was nothing to remove.

### The pool-radius calibration stands

§"Calibration" above is untouched by this. The equilibrium radius reproduces
six reported pool radii with a median ratio of 1.11 and no free parameter, and
that comparison uses lengths rather than concentrations. It remains available
to any successor.

### What the deficiency actually is

**A horizontal two-phase cryogenic jet at 0.83 kg/s is over-diluted by a
factor of 2.6 at 30 m, independently of humidity.** Test 3 at 0.73 kg/s
vertically downward is not. The two differ in orientation, and the model
treats both as `HorizontalJet` — so whatever is wrong is wrong specifically
for the case the class is actually meant for.

`PREREG_lh2_wall_jet`, proposed on the strength of the results above, is
withdrawn before registration: it addresses the vertical-down source, which
this addendum shows does not need addressing.
