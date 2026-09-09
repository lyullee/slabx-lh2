# Pre-registration: coupling the cloud width to its rise

**Registered 2026-08-21, before the term was written and before any
comparison.** Nothing above the `RESULTS` line is to be edited afterwards.

---

## What five registrations have established

| brake | registration | outcome |
|---|---|---|
| ground reflection hid the lift-off | `PREREG_lh2_liftoff` | rejected; removing reflection entirely still gives ground/max 0.88-0.99 |
| the cloud is too deep | `PREREG_lh2_depth` | rejected in the opposite direction: it rises too much |
| vertical drag missing before lift-off | `PREREG_lh2_grounded_drag` | rejected; the window is 1.3 m and 0.15 % of the momentum |
| entrainment that responds to the rise | `PREREG_lh2_rise_entrainment` | rejected; 17 % on the rise, and the source term decayed *slower* |
| added mass with an oblate-spheroid shape | `PREREG_added_mass` | rejected; spread saturates at 1.46, no `C_A` fits |

The last of these is the informative one, and it produced an algebraic result:

    dGw/dx = g (rho_a - rho) B h
    rho_a - rho ~ rho_a m,  m = q/R,  R = rho u B h
    =>  (rho_a - rho) B h  ~  rho_a q / (rho u)

**The buoyancy source term is the conserved buoyancy flux divided by the wind
speed, and contains no `R`.** Entrainment cannot reduce it: it lowers the
deficit and raises `B h` in near-compensating proportion. Measured — doubling
the entrainment made the deficit decay 34 % faster and the source term 8 %
faster.

So the brake has to act on the other side of `w_c = Gw / R`.

## The hypothesis

**A bent-over buoyant plume limits its own rise because its width is set by
its height.** Entrainment across the perimeter makes `b ~ beta z`, so
`R ~ rho u beta^2 z^2`, and

    dz/dx = w/u = Gw/(R u) ~ x / z^2   =>   z ~ x^(2/3)

which is Briggs. **`slabx` has no such coupling.** Once the cloud lofts, `B`
continues to be set by gravity spreading and ground-level ambient entrainment
(EQ 7, `f[1] = (sqrt3 (rho_a/rho) V_e + V_g) / u`), and nothing tells it that
it is now a plume at altitude.

Measured on NASA Test 6:

| x [m] | `z_c` [m] | `B` [m] | `beta z_c` [m] | **`B/(beta z_c)`** |
|---|---|---|---|---|
| 34 | 103.7 | 6.9 | 41.5 | **0.167** |
| 100 | 246.4 | 10.5 | 98.6 | **0.107** |
| 200 | 369.0 | 16.3 | 147.6 | **0.111** |
| 400 | 482.9 | 26.6 | 193.1 | **0.138** |

**The cloud is six to nine times narrower than a plume of its own height**,
and the rise exponent is

    z_c ~ x^1.220        against Briggs's x^0.667

**The rise runs away because the cloud never grows the inertia that would stop
it.**

## The intervention

Once the cloud is lofted and rising, add the plume-spread contribution to the
cross-wind entrainment velocity, so that the width equation gains
`beta dz_c/dx`:

```python
if lofted and w_c > 0:
    dB/dx  gains  beta * w_c / u                # plume spread
```

implemented through `V_e`, because in EQ 7 the width slope is
`(sqrt3 (rho_a/rho) V_e + V_g)/u`, so the required addition is

    V_e  +=  beta * w_c * rho / (sqrt3 * rho_a)

`V_e` also appears in EQ 2a, so the widening entrains — which is the physical
content of the coupling and must not be suppressed.

**Declared before the run:**

- **`beta` = 0.4**, the value already in `COEFFS.briggs_beta0`, which is
  Briggs's bent-over plume spread parameter. **No new coefficient.**
- The gate is `z_c > h/2` (`is_lofted`, the model's own switch) **and**
  `w_c > 0`, so a grounded or sinking cloud is untouched.
- The term is added to `v`, not to `v_front`, so it enters both the width and
  the mass equation.

## Predictions

| # | Prediction | Criterion |
|---|---|---|
| **P-W1** | The rise follows the bent-over plume law | fitted exponent of `z_c ~ x^n` over 10 to 100 m falls to **0.6 - 0.9**; currently 1.220 |
| **P-W2** | The width catches up with the height | `B/(beta z_c)` at 100 m reaches **0.5 - 2.0**; currently 0.107 |
| **P-W3** | The rise is bounded where it was observed | NASA cloud top at the 33.8 m ring within a factor of **2** of the observed 20 m; currently 4.98 |
| **NC1** | The dense limit is untouched | ten LNG pool trials **bit-identical** |
| **NC2** | The passive limit is untouched | Prairie Grass **bit-identical** |
| **NC3** | The trials inside the premise barely move | FFI Tests 1, 3, 4, 7 arc concentrations change by **< 10 %** |

**P-W1 is the discriminating one.** P-W3 could be satisfied by anything that
dilutes harder. Only a width that grows with height produces the `x^(2/3)`
exponent, and the exponent is a shape rather than a level.

## What would falsify

**P-W3 passing while P-W1 fails**: the rise has been bounded by something other
than the claimed mechanism. Not adopted.

**P-W1 passing while P-W2 fails**: the exponent came out right without the
width coupling that is supposed to produce it. Not adopted — that would mean
the term is acting through EQ 2a dilution rather than through inertia.

**NC3 failing**: the term reaches trials whose `w_c/u` is 0.03, where the
model already matches. `PREREG_lh2_rise_entrainment` failed exactly here at
15.18 %, and this term is gated on `is_lofted` as well as on `w_c`, which the
previous one was not. If it still leaks, the gate is not the issue and the
formulation is.

**The exponent falling below 0.6**: over-corrected — the cloud is now being
held down rather than following the plume law.

## What must not happen

**`beta` is not to be swept.** It is 0.4, the value already in the
coefficient table. Document 18 §18.8 measured what fitting costs on this
dataset: no coefficient reproduces the orientation difference at all, fitting
the bias to LH2 takes the LNG FAC2 from 0.90 to 0.20, and within LH2 alone the
between-trial spread grows from 4.71 to 5.50 as the bias is fitted out.

**Added mass stays off.** `c_added_mass` = 0, not swept. Its shape function was
rejected on its own evidence and this registration does not revisit it.

**An improved aggregate is not a result.** If P-W1 and P-W2 do not both pass,
this is not adopted however good the concentration statistics become.

## What this does not claim

It does not repair the premise. `slabx` marches in `x`, which presumes downwind
advection, and `w_c/u` reaches 3.68 on NASA Test 6. If this term succeeds it
will be because it lowers `w_c/u` back toward the range where the premise
holds, which is a consequence and not a justification. Document 22 §22.10's
applicability statement stands either way.

If it succeeds it also does **not** mean the model is validated for buoyant
releases: the target is a single reported plume extent, second-hand from
Ichard et al. (ICHS 2009) reading Witcofski & Chirivella, with NASA TM-83131
not obtained. **Grade C.**

## Scope

NC1, NC2, P-W1 and P-W2 are deterministic. P-W3 rests on one trial.

The default stays as Ermak wrote it. Plume-spread coupling is a variant, off
unless asked for.

---

## RESULTS

*(appended 2026-08-21 after the run; nothing above this line was edited)*

### Negative controls, run first

| | bit-identical | max abs difference in `z_c` |
|---|---|---|
| **NC1** LNG pool (Burro 8 deck) | **yes** | 0.000e+00 |
| **NC2** passive SO2 (Prairie Grass) | **yes** | 0.000e+00 |

### NC3 — PASSED, exactly

FFI Tests 1, 3, 4, 7, all twelve arc points, z = 1 m: **0.00 % change on every
one.** The gate is `is_lofted`, and FFI never lofts — `z_c` stays below `h/2`
across the whole domain. `PREREG_lh2_rise_entrainment` leaked 15.18 % here
because it was gated on `w_c` alone.

### P-W1 — PASSED

Fitted exponent of `z_c ~ x^n` over 10 to 100 m:

| | exponent |
|---|---|
| off | 1.200 |
| **on** | **0.869** |
| Briggs bent-over plume | 0.667 |

Criterion was 0.6 to 0.9.

### P-W2 — PASSED

`B / (beta z_c)` at the 100 m arc: **0.107 -> 0.727**. Criterion was 0.5 to
2.0. The cloud now widens roughly as a plume of its own height.

### P-W3 — FAILED, narrowly

NASA cloud top at the 33.8 m ring:

| | height [m] | vs observed 20 m |
|---|---|---|
| off | 99.56 | 4.98x |
| **on** | **44.04** | **2.20x** |

Criterion was within a factor of **2**. It came in at **2.20**. **This is
recorded as a failure.** `beta` is not to be swept and is not swept; the
criterion was fixed before the run and it was missed by ten per cent.

### The trajectory now sits on the bent-over plume law

| x [m] | Briggs | slabx off | **slabx on** | observed | `B` off | `B` on |
|---|---|---|---|---|---|---|
| 9.1 | 14.6 | 10.5 | **8.7** | ~20 | 5.3 | 7.8 |
| 18.3 | 23.2 | 43.2 | **24.2** | ~20 | 5.9 | 14.5 |
| 33.8 | 35.0 | 97.3 | **41.8** | ~20 | 6.8 | 22.3 |
| 40.0 | 39.1 | 116.8 | **47.4** | ~20 | 7.2 | 23.3 |

**`slabx` with the coupling agrees with Briggs to within 20 %, where before it
was 2.8 times Briggs at the same arc.** Both remain about twice the reported
observation.

That is the expected place for the residual to sit. Briggs is itself a
bent-over formula, and `max w_c/u` on this trial is **2.134** after the
coupling — down from 3.675 but still above one. **Both models are being
evaluated outside the premise they share**, which is what document 22 §22.4
says and what the observation being *below* both of them indicates.

### The old §22.3 metric moved the wrong way, and should have

Deficit decay over 6 to 561 m went 434x to **1206x**, while `dGw/dx` decay went
11.9x to 16.2x, so the ratio worsened from 36.5 to 74.4.

That is not a defect here. `PREREG_lh2_rise_entrainment` established
algebraically that `dGw/dx ~ rho_a q/(rho u)` carries no `R`, so no
intervention can reduce it. **This one was never aimed at `Gw`.** It works on
`R`, and `R` is what `w_c = Gw/R` divides by: `w_c` at the 34 m ring falls from
7.78 to **2.15 m/s**.

### Status

| | |
|---|---|
| NC1, NC2, NC3 | **PASS** |
| P-W1 rise exponent | **PASS** — 1.200 to 0.869 |
| P-W2 width coupling | **PASS** — 0.107 to 0.727 |
| P-W3 rise height | **FAIL** — 2.20x against a criterion of 2.0x |

**The mechanism is confirmed; the registered magnitude criterion was missed.**
The registration's necessary condition for adoption — that P-W1 and P-W2 both
pass — is met, and P-W3 is not. This is the first of six registrations in this
line to pass its discriminating predictions, and it is not to be written up as
a success without the P-W3 failure attached.

### What this establishes

**The runaway was the absence of a width-height coupling, not a missing
brake.** Five earlier registrations looked for something to oppose the rise —
reflection, depth, drag, entrainment, added mass. None of them could work,
because the buoyancy source term is a conserved flux that nothing can reduce.
What limits a real plume is that it grows the inertia to stop itself, and
`slabx` had no path by which rising made the cloud wider.

The intervention adds one term to `V_e`, gated on the model's own lift-off
switch, with a coefficient already in the table. It is inert on every dense
trial, on the passive limit, and on all four LH2 trials that stay grounded.

### What it does not establish

The premise is not repaired: `w_c/u` is still 2.13. The remaining factor of two
against the observation is shared with Briggs and is most likely the premise,
not the coupling — but that is an inference from one trial with second-hand
provenance, not a measurement.

**Do not enable this by default on the strength of one trial.** The next step
is the E3.5 far-field stands, where twenty trials span the diagnostic from
0.043 to 1.093 and the vertical gradient can be compared across them.

### Reproduction

```bash
cd lh2mod
python3 run_pw.py
```


---

## ADDENDUM — re-evaluated under the corrected baseline, and failed

*(appended 2026-08-22. The criteria of P-W1 and P-W2 were fixed in the
registration above, before any of this. What changed is the baseline: the
water sublimation correction of document 23 was adopted afterwards.)*

### Why re-evaluate

The registration was run before `slabx_lh2.water_ice` existed. The correction
releases the enthalpy of sublimation in the cold cloud, so the cloud is lighter
and the buoyancy source term the coupling has to offset is **larger**. The two
modules were each verified alone and never together on these predictions.

### All four NASA trials, both modules

Witcofski & Chirivella (1984) give four usable trials at a fixed 5.7 m3 spill
with wind from 1.6 to 6.3 m/s, which the registration could not use because the
original paper had not been obtained.

| test | u [m/s] | `w_c/u` | off | water only | width only | **both** | P-W2 (both) |
|---|---|---|---|---|---|---|---|
| 2 | 1.6 | 4.74 | 1.283 | 1.336 | 1.260 | **1.275** | 0.252 |
| 6 | 2.2 | 2.48 | 1.236 | 1.284 | 0.904 | **1.068** | 0.462 |
| 4 | 3.6 | 1.29 | 1.188 | 1.281 | 0.891 | **1.053** | 0.846 |
| 5 | 6.3 | 0.61 | 1.137 | 1.233 | 0.923 | **1.055** | 1.378 |

| | |
|---|---|
| **P-W1** exponent in 0.6 - 0.9 | **0 / 4** |
| **P-W2** `B/(beta z_c)` in 0.5 - 2.0 | **2 / 4** |

**With the water correction active, the coupling no longer brings the exponent
into the registered band.** On Test 6, which the registration used, it goes
0.883 without the correction and **1.047 with it**. The original P-W1 pass was
obtained under a baseline that has since been superseded, and is withdrawn.

Document 24 section 24.3 reported the interaction between the two modules as
about 6 %. That was measured on the NASA cloud **top**. On the rise exponent it
is not 6 %, and the earlier figure should not be read as covering this.

### The residual is not unexplained

Writing the rise as `dz/dx = Gw/(R u)` with `Gw ~ x` and `R = rho u B h ~ z^s`
gives `z^(s+1) ~ x^2`, so

    n = 2 / (s + 1),      s = dlnB/dlnz + dlnh/dlnz

Briggs is `s = 2`: **both** semi-axes proportional to the height. Measured on
the model's own output, with both modules active:

| test | `dlnB/dlnz` | `dlnh/dlnz` | `s` | predicted `2/(s+1)` | fitted `n` |
|---|---|---|---|---|---|
| 2 | 0.390 | 0.229 | 0.618 | 1.236 | 1.275 |
| 6 | 0.470 | 0.348 | 0.818 | 1.100 | 1.068 |
| 4 | 0.592 | 0.421 | 1.013 | 0.994 | 1.053 |
| 5 | 0.521 | 0.492 | 1.013 | 0.994 | 1.055 |

**The prediction matches the fit to within 6 % on all four** (3.0, 3.1, 5.7
and 5.9 %), which confirms
the algebra against the model rather than against an assumption.

So the shortfall is quantified and located:

- **the depth is not coupled to the rise at all.** `dlnh/dlnz` is 0.23 to 0.49
  where Briggs needs 1.0, and nothing in the intervention touches EQ 8
- **the width is coupled only partway.** `dlnB/dlnz` is 0.39 to 0.59, because
  the gravity-spreading and ground-entrainment terms of EQ 7 remain and dilute
  what the coupling adds

A real bent-over plume has a roughly circular cross-section and both semi-axes
grow as `beta z`. SLAB carries `B` and `h` in separate equations and this
intervention touched one of them.

Available as `slabx_lh2.diagnostics.rise_scaling`.

### What is not being done

**`beta` is not raised to close the gap.** The registration forbids sweeping
it, and raising it would buy the exponent at the cost of the free parameter
this work has avoided throughout. The gap is a missing term, not a
mis-set coefficient — `s` is short by a whole unit, which no rescaling of one
term supplies.

### Every trial is outside the premise

`max w_c/u` is 0.61 to 4.74; three of four exceed 1. **The registration's
target sits outside the applicability envelope this project established in
document 22**, and so did the original single-trial evaluation at 3.68.

There is no dataset that measures the rise of a lofted cloud from **inside**
the premise: NASA has the vertical towers and is outside it, while FFI, E3.5
and RR986 are inside it and none of them reports a cloud height. **The
quantitative test cannot be performed with what exists.**

### What may be claimed, after this

**Not** that the coupling reproduces the bent-over rise law. What survives:

1. **a mechanism argument** — the buoyancy source term is a conserved flux
   that entrainment cannot reduce (`PREREG_lh2_rise_entrainment`), so what
   limits a real plume is the inertia it grows, and the model had no path by
   which rising made the cloud larger
2. **negative controls** — bit-identical wherever the gate does not open
3. **direction, at four conditions** — `B/(beta z_c)` improves monotonically
   on every trial: 0.039 to 0.252, 0.079 to 0.462, 0.179 to 0.846, 0.501 to
   1.378
4. **a quantified residual** that names the missing term

**Status: retained as a physically motivated partial correction, not as a
validated one.** It stays off by default, as the registration required.

---

## ADDENDUM 2 — a second mechanism, from EFFECTS

*(appended 2026-08-22. The band of P-W1 is the one fixed in the registration
above. This is a re-evaluation with a term added, not a new hypothesis.)*

Mack & Boot's extension of EFFECTS (*J. Loss Prev. Process Ind.*, 2023) reports
the same symptom in a different code — "for strongly buoyant plumes, it was
observed that vertical plume speeds are overpredicted by some integral models"
— and takes a different route. Rather than the added-mass concept, which
reduces the buoyancy term, they add form drag on the plume as a bluff body in
crossflow:

    C_d  = C_d0 + C_d1 (1 - AR),           AR = h / B
    dF_z = C_d (rho_a / 2) cos^2(phi) w^2 B dx

For a continuous release **the coefficients are not fitted**: `C_d0` = 1.17 is
the classical circular-cylinder drag coefficient and `C_d1` = 1.2 the increase
towards a flat plate over the aspect-ratio range, from numerical results. The
paper states that only the *instantaneous*-release coefficients were adapted
against experiment.

Implemented as `slabx_lh2.vertical_drag` with those values. **Nothing tuned.**

### Result, four NASA trials

| test | u [m/s] | baseline | width only | drag only | **both** | P-W1 |
|---|---|---|---|---|---|---|
| 2 | 1.6 | 1.336 | 1.275 | 1.319 | **1.244** | FAIL |
| 6 | 2.2 | 1.284 | 1.068 | 1.173 | **0.978** | FAIL |
| 4 | 3.6 | 1.281 | 1.053 | 1.017 | **0.908** | FAIL |
| 5 | 6.3 | 1.233 | 1.055 | 0.998 | **0.904** | FAIL |

**P-W1 (0.6 - 0.9): 0/4.** Tests 4 and 5 miss by 0.008 and 0.004 — under half
a percent — and are still failures.

### What it shows

**The two are independent and both act in the right direction.** Drag alone
lowers the exponent from 1.23 - 1.34 to 1.00 - 1.32; the width coupling alone
to 1.05 - 1.28; together to 0.90 - 1.24. They do not overlap, which is what
two different mechanisms against one symptom should look like.

**The trend with wind is the useful part.** The pair gets closest where the
premise is least violated — 0.904 at `w_c/u` = 0.59 and 0.908 at 1.17, against
1.244 at 5.14. The two trials nearest the registered band are the two nearest
the applicability boundary.

### What is not being done

**The coefficients are not adapted.** Mack & Boot's own caveat invites it —
"coefficients might have to be adapted due to the fact that plumes are gaseous
objects with density variations" — and a few per cent on `C_d1` would carry
both trials into the band. That is precisely the move this work has refused
seven times, and a pass bought that way would mean nothing.

**Status unchanged: retained as a physically motivated partial correction.**

### A patching defect found on the way

`slabx.core.plume` does `from ..submodels.entrainment import fluxes`, so it
holds its own reference to the function. Patching the submodule alone had
**exactly zero effect**, and the first run of this comparison returned
identical numbers with the drag "on" without any error. Both names are now
swapped, and `tests/test_modules.py::TestVerticalDrag::test_patches_both_names`
pins it.

**A monkey-patch that silently does nothing is the worst kind**: it looks like
a clean negative result.

---

## ADDENDUM 3 — a factor of two in the drag, corrected

*(appended 2026-08-22)*

`B` in Mack & Boot's drag term is the **full projected width**, and
`slabx_lh2.vertical_drag` was reading it as slabx's half-width.

Two independent readings fix the definition. `AR = 1` is stated to be the
circular cylinder, which requires `H` and `B` to be the same kind of measure,
and `H` in slabx is the full cloud height. And the drag on a cylinder per unit
length is conventionally `C_d (rho/2) v^2 D` with `D` the diameter, which is
the form the paper writes.

So both the coefficient and the force were wrong, in opposite directions:
`AR` was twice too large, which clipped the coefficient to its cylinder value,
and `B` was half what it should be.

### Corrected

| test | u [m/s] | width only | +drag, **as published before** | +drag, **corrected** | P-W1 |
|---|---|---|---|---|---|
| 2 | 1.6 | 1.275 | 1.244 | **1.304** | FAIL |
| 6 | 2.2 | 1.068 | 0.978 | **1.053** | FAIL |
| 4 | 3.6 | 1.053 | 0.908 | **0.925** | FAIL |
| 5 | 6.3 | 1.055 | 0.904 | **0.862** | **PASS** |

**P-W1 goes from 0/4 to 1/4, and three of the four get worse.**

The earlier numbers sat close to the band — 0.978, 0.908, 0.904 against a
limit of 0.9 — and ADDENDUM 2 recorded that they missed "by under half a per
cent". **They were that close because of the error.** With `B` read correctly
only the windiest trial lands in the band.

**The correction stands regardless of which way it moved the result**, which
is the whole reason for checking a definition against the source rather than
against the outcome.

### Status

`vertical_drag` is **exploratory and not adopted**. It belongs in
supplementary material as a comparison of two candidate mechanisms, not in a
results section.
