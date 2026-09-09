# PREREG — the depth follows the rise once the cloud lofts

**Registered 2026-08-24, before implementation.** Nothing above the `RESULTS`
line is to be edited afterwards.

## What was wrong with the rejected attempt

`PREREG_lh2_depth_cap` held the depth at the passive-dispersion ceiling for
the whole trajectory. NC3 failed on three of four downward trials and P-D4
failed on all six: **the cloud became a thin ribbon that kept climbing** and
left the sensor plane, because the depth was frozen while `z_c` grew.

That was an error in the closure, not in the diagnosis. The depth really is
three times the passive limit at 30 m.

## The physics that was left out

For a bent-over buoyant plume the cross-section is not free: the radius is
proportional to the rise height,

    b = beta * z

which is the Morton-Taylor-Turner result Briggs's 2/3 law is built on. It
follows that `R ~ z^2`, hence `s = dln(Bh)/dlnz = 2`, hence the rise exponent
`n = 2/(s+1) = 2/3`.

**The rejected cap violated this.** Holding `h` fixed drives `dlnh/dlnz`
towards zero, which is the opposite of the 1.0 the plume closure requires.

So the depth has two regimes and the earlier attempt implemented only one:

| | what sets the depth |
|---|---|
| **grounded** | ambient turbulence -- the passive layer is the ceiling |
| **lofted** | the plume's own entrainment -- `h` grows with `z` |

## The change

    while grounded   h <= k * sigma_z(x)          as before
    once lofted      dh/dx >= 2 * beta * w_c / u  the plume closure

`beta` is `coeffs.briggs_beta0`, **already in slabx's coefficient table and
already used by `plume_width` for the width**. `k = 1.5` as before. **Nothing
is fitted and nothing will be adjusted after the run.**

The two are combined as a floor and a ceiling, not as an override: the depth
may not exceed what turbulence can mix while the cloud is grounded, and may
not grow slower than the plume closure once it is not.

## Negative controls -- run FIRST, any failure ends it

**NC1.** Ten LNG pool trials: change **below 1 %**. Dense clouds neither reach
the ceiling nor loft, so both branches should be inactive.

**NC2.** Prairie Grass passive: **bit-identical**.

**NC3.** The four downward FFI trials at 30 m: **every ratio within 0.8 to
1.25**. They are 0.94 to 1.17 now. **This is what killed the last attempt and
it is the binding control again.**

**NC4.** The 50 and 100 m arcs on all six trials: **within 0.7 to 1.5**. The
last attempt collapsed these to 0.00 to 0.45 and that must not recur.

**NC5.** No trial changes its applicability status.

## Predictions

**P-P1.** The two horizontal trials reach a 30 m ratio of **0.6 or better**
(now 0.37 and 0.39).

**P-P2.** `dlnh/dlnz` on the four NASA trials rises **above 0.7** (now 0.23 to
0.49). **This is the discriminating one**: it is the quantity the plume
closure is supposed to fix, and it was registered and measured before any of
this work.

**P-P3.** The NASA rise exponent falls **below 0.95** on at least three of the
four trials (now 1.05 to 1.28, Briggs 0.667).

**P-P4.** The LFL bracket stays at **five of six** and the required factor
stays **below 1.25**.

## What would falsify it

If NC3 or NC4 fails, rejected, whatever the predictions do.

If P-P2 fails while the negative controls pass, the depth does not respond to
the plume closure and the two-regime picture is wrong.

**If P-P1 passes but P-P2 fails**, the near field has been fixed by something
other than the coupling, and the change is a fit rather than a correction.
Reject it.

## RESULTS

*(appended 2026-08-24 after the run; nothing above this line was edited)*

### Negative controls -- **FAILED**, and the change is rejected

| | criterion | result | |
|---|---|---|---|
| **NC1** LNG pool, ten trials | < 1 % | **36.1 %** | **FAIL** |
| **NC2** Prairie Grass passive | bit-identical | differs | **FAIL** |

The registration says any negative-control failure ends it. **It is
rejected**, and the predictions were not evaluated.

### Where the failure comes from -- not the plume branch

The plume floor never fires on either control. On Prairie Grass the cloud is
`is_lofted` on **0 of 51** rows, buoyant on **0 of 51**, and `w_c` is exactly
zero throughout. The second regime is inert there, as intended.

**The failure is in the first regime, which was carried over unchanged from
the rejected registration.** A pool source has a finite depth at the nozzle,
and the passive ceiling near the source is not:

| x | `1.5 sigma_z` |
|---|---|
| 1 m | **0.09 m** |
| 10 m | 0.90 m |
| 30 m | 2.64 m |

A metres-deep pool source is crushed to centimetres in its first step. The
FFI jets have a source a few centimetres across and were bitten far less,
which is why the LH2 numbers looked plausible while the dense-gas validation
was being destroyed.

### What this rules out, and what it does not

**A passive-dispersion ceiling applied from the source is dead.** It cannot
be repaired by adjusting `k`: the problem is that `sigma_z(x)` goes to zero
at the source and a real cloud does not.

**It does not rule out the diagnosis.** The depth is still three times the
passive limit at 30 m and that is still the whole of the horizontal-jet
under-prediction. Nor does it rule out the plume closure in the second
regime, which was never reached.

A third attempt, if there is one, has to start the ceiling from a **virtual
origin** set so that it equals the source depth at the source, rather than
from `x = 0`. **Register it separately and re-run every control against a
version whose effect on the run has been demonstrated.**
