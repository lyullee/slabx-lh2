# Withdrawal: PREREG_lh2_buoyant_rise

**Withdrawn 2026-08-21, before any comparison was run.**

The predictions in `PREREG_lh2_buoyant_rise.md` are not edited. They stand as
written and are withdrawn as a whole. This file records why.

---

## What the registration assumed

That `slabx` has no buoyant-rise branch, so that adding one would be the
intervention under test:

> `slabx` raises `BuoyantRiseNotImplemented` for a positively buoyant vertical
> jet, and has no lift-off criterion for a grounded buoyant cloud. [...] every
> LH2 release sits in the branch that is missing.

## What reading the source showed

**The first sentence is wrong.** `BuoyantRiseNotImplemented` lives only in
`core/vertical_jet.py`, in the source-region plume-rise solve for IDSPL = 3
(a stack release). The plume core has a buoyant branch already:

```python
lofted = htp > h
if inside_source:
    if rho > atm.rho: v_g = ...
elif lofted or rho <= atm.rho:            # LH2 is always here
    w_c = ew * (Gw + R0 * prev.w_c) / R   # recovered from EQ 6a
```

`f[6] = -g * d_rho * B * h`, and `d_rho < 0` for LH2, so `Gw` accumulates
positive and the cloud rises. Measured on FFI Test 4:

| x [m] | w_c [m/s] | z_c [m] | h [m] | sigma_z [m] |
|---|---|---|---|---|
| 19.4 | -0.0003 | 0.49 | 4.48 | 2.31 |
| 40.7 | +0.053 | 0.57 | 6.73 | 3.55 |
| 85.4 | +0.167 | 1.41 | 10.10 | 5.02 |
| 123.7 | **+0.175** | **2.54** | 12.48 | **5.74** |

`w_c > 0` on 18 of 41 rows. FFI's releases are horizontal (Test 4) or
vertically downward (Tests 1, 3, 7); none is a stack release, so none reaches
the unimplemented branch.

**P-B4 is therefore satisfied before the intervention** — `z_c` at 100 m is
2.5 m against a threshold of 5 m — and **P-B1 has no intervention to test.**

## The mechanism has moved

The vertical profile is a **ground-reflected** Gaussian. With `z_c` = 2.3 m
and `sigma_z` = 5.5 m at the 100 m arc:

| z [m] | direct | **image** | sum |
|---|---|---|---|
| 0.1 | 0.952 | **0.940** | **1.892** |
| 1.8 | 0.999 | 0.804 | 1.803 |

The image term lifts the ground value above the value at the centre height.
**While reflection is applied and `sigma_z` exceeds `z_c`, the concentration
maximum cannot leave the ground at any rise height.** The measurement at
100 m rises with height (0.6, 0.7, 0.8 %vol at 0.1, 1.0, 1.8 m).

So the deficiency is not the rise. It is that a cloud which has detached is
still being reflected off the ground it has left.

## Why this withdrawal is legitimate

**Nothing had been run.** The registration was written before the branch was
to be implemented; the correction came from reading
`core/plume.py` and `core/vertical_jet.py`, not from a comparison. No
prediction is being revised in the light of a number it was meant to predict.

Had this been discovered *after* the run, the correct action would have been
to report P-B1 as failed and P-B4 as passed, and to open the successor
registration on that basis — which the original text specifies. The outcome
is the same registration; only the honesty of the route differs, and the
route is recorded here so a reader can check it.

## What replaces it

`PREREG_lh2_liftoff.md`, registered the same day, testing the reflection
under a detached cloud rather than the rise itself.

## What this adds to the record

**§C7a, ninth self-error.** The project documentation states that buoyant
rise for light gases is unimplemented (document 01 §1.12, `scope.py`,
`LIMITATIONS.md` §1). That is true of `VerticalJet` and false of the plume
core, and the two were not distinguished anywhere. Document 18 §18.5 then
reported that `z_c` tracks the measured peak height and called it
surprising — it was not surprising, it was the branch working.

Same shape as the others: a summary that was right about one thing and read
as though it were right about a larger thing, surviving because nothing
depended on the difference until now.
