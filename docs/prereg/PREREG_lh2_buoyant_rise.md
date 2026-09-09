# Pre-registration: buoyant rise and lift-off for LH2 releases

**Registered 2026-08-21, before the branch was written.**
Nothing above the `RESULTS` line is to be edited after the run.

---

## The claim under test

`slabx` raises `BuoyantRiseNotImplemented` for a positively buoyant vertical
jet, and has no lift-off criterion for a grounded buoyant cloud. Document 18
reports that an LH2 cloud is buoyant across the whole mixing range
(`rho/rho_a` = 0.94 - 1.008 through the model's own EQ 10), so every LH2
release sits in the branch that is missing.

Two observations frame the test.

**The trajectory already tracks the measurement.** On FFI Test 4 the profile
centre height `z_c` is 0.51, 0.68 and 1.83 m at the 30, 50 and 100 m arcs,
against a measured concentration maximum sitting at 0.1, 1.0 and 1.8 m. The
concentration profile does not show it, because at 100 m the cloud depth is
about 12 m and `sigma_z = (h - z_c)/sqrt3` is near 6 m, which flattens the
profile over the 0 - 1.8 m the sensors cover.

**A free buoyant jet gets it badly wrong.** HyRAM+ 6.1, which carries
buoyancy in the momentum balance but has no ground boundary, puts the plume
centreline at 99.9 m at the same arc — a factor of 55.

So the question is not whether rise is missing. It is whether adding a
published rise branch improves the profile **without** producing the free-jet
failure.

## What is being added

**A1 — the Briggs branch.** The coefficients are already externalised and
unused: `briggs_beta0` = 0.4, `briggs_beta1` = 1.2, `briggs_buoyant` = 1.2.
They are taken as published and not adjusted.

**A2 — a lift-off criterion.** Hall & Walker (2000), as reported in
AEAT/NOIL/27328006/001:

    onset of rise    F / (W u^3)  ~ 0.01
    lift-off         F / (W u^3)  ~ 0.035     (ground concentration falls to
                                               10-20 % of the maximum)

Both numbers are taken as published. The harness that reads them already
exists from `PREREG_added_mass`.

**Free parameters: zero.**

## Predictions

| # | Prediction | Criterion |
|---|---|---|
| **P-B1** | The branch moves the height of the concentration maximum so that it follows the arcs | on Test 4 the maximum sits at **z = 1.0 m at 50 m** and **z = 1.8 m at 100 m**; it currently sits at the lowest sensor at every arc |
| **P-B2** | The lift-off criterion reproduces the measured threshold | at F/(Wu³) = 0.035 the ground concentration is **10 - 20 %** of the maximum |
| **P-B3** | The effect is confined to the far field | Test 4 concentration at 30 m changes by **< 10 %** |
| **P-B4** | Ground attachment is retained — the free-jet failure does not appear | `z_c` at 100 m stays **below 5 m** (HyRAM+ gives 99.9 m, measurement 1.8 m) |
| **NC1** | A dense release has no buoyant branch to enter | the ten LNG pool trials are **bit-identical** |
| **NC2** | Added mass stays off | `c_added_mass` = 0 throughout; no sweep is run |

## What would falsify the diagnosis

If **P-B1 fails while P-B4 passes**, the deficiency is not the rise but the
profile depth: `z_c` was already right and `sigma_z` is what hides it. In
that case this branch is not the answer and `PREREG_lh2_depth` is written
instead. That outcome is to be reported as a failure of this prediction, not
folded into a later test.

If **P-B4 fails**, the branch has reproduced the free-jet behaviour and must
not be adopted whatever it does to the aggregate.

## What must not happen

**The added-mass term is not to be reintroduced.** `PREREG_added_mass` found
that the oblate-spheroid `B/h` shape function is the wrong shape function
rather than a mis-scaled one: the width spread saturates at 1.46 and tripling
`C_A` does not improve it. Implementing buoyant rise creates an obvious
temptation to reach for that term to suppress the rise. Doing so would revive
a hypothesis this project has already rejected on its own evidence.

**The Briggs coefficients are not to be fitted.** Document 18 §18.8 measures
what fitting costs here: no coefficient produces the 2.69-fold orientation
difference at all, fitting the bias to LH2 takes the LNG FAC2 from 0.90 to
0.20, and within LH2 alone the between-trial spread grows monotonically from
4.71 to 5.50 as the bias is fitted out. There is no version of this that
works.

**An improved aggregate is not a result.** In `PREREG_froude` the Robins
closure was better than the original on every aggregate measure and was
rejected because the mechanism it was introduced to fix was not fixed. The
same rule applies: if P-B1 and P-B4 do not both pass, the branch is not
adopted however good FAC2, MG or VG become.

## Scope of the comparison

Four unignited FFI trials, three arcs each. **n = 4.** By document 07 §7.3
the detectable MG ratio at this sample size is about 1.6, so any result here
is graded **C** — direction only — unless it is deterministic. P-B4 and NC1
are deterministic and are not subject to that limit.

FFI Test 2 is excluded: the wind was from 82 degrees and the array was moved,
leaving radii of 9.01, 11.04 and 30 m rather than the 30/50/100 m grid.

The default stays as Ermak wrote it. The branch is a variant.

---

## RESULTS

*(to be appended after the run; nothing above this line is to be edited)*
