# PREREG — a passive-dispersion ceiling on the cloud depth

**Registered 2026-08-24, before the change was implemented or run.**
Nothing above the `RESULTS` line is to be edited afterwards.

## Provenance of the idea, stated because it matters

**The closure was chosen after looking at the answer.** The cross-section of
the FFI test 6 cloud at 30 m was decomposed:

| | area | width | depth |
|---|---|---|---|
| implied by the measured 21 vol% | 13.3 m2 | -- | -- |
| Pasquill-Gifford D, `pi sy sz` | 13.3 m2 | 7.2 m | 2.6 m |
| the model | 63.8 m2 | 8.1 m | **7.8 m** |

The width is right to 10 %; **the depth is three times too large**, and that
alone accounts for the factor of 2.6 by which the horizontal-jet maximum is
under-predicted. Passive Gaussian dispersion was then observed to match the
required area to 1 %, and that observation is why `sigma_z` is the ceiling
proposed here rather than something else.

**This is not a free parameter** -- Pasquill-Gifford `sigma_z` is a published
correlation and nothing in it will be fitted. But the reader should know the
order in which this happened.

## What is independent of that

`docs/27` registered and measured `dlnh/dlnz = 0.23 to 0.49` on the **NASA**
trials against a required 1.0, i.e. the depth does not follow the rise. That
was recorded before any of this and comes from a different dataset and a
different quantity. **The present finding confirms it from the concentration
side.**

## The change

The cloud depth is capped at what passive turbulent dispersion can produce:

    h <= k * sigma_z(x, stability)

with `sigma_z` the Pasquill-Gifford D curve as already implemented in slabx,
and `k` fixed at **1.5** before any run -- the standard conversion from a
Gaussian standard deviation to a top-hat depth, and the same factor slabx
already uses elsewhere for the width. **`k` will not be adjusted.**

The rationale is that turbulent diffusion sets a physical ceiling on how thick
a passively-dispersing layer can be at a given distance; a cloud cannot be
thicker than the turbulence can mix it, whatever the entrainment closure says.

## Negative controls -- run FIRST, any failure ends it

**NC1.** Ten LNG pool trials, LFL distance: change **below 1 %**. The
published dense-gas validation must not move. Dense clouds are shallow and
should not reach the ceiling at all; if they do, the ceiling is wrong.

**NC2.** Prairie Grass passive SO2: **bit-identical**. A passive release is
already at the passive limit and the cap must be inactive.

**NC3.** The four downward FFI trials (1, 3, 5, 7) at the 30 m arc:
**every ratio stays within 0.8 to 1.25**. They are currently 0.94 to 1.17 and
**they are the thing most likely to break**. This is the binding control.

**NC4.** No trial changes its applicability status.

## Predictions

**P-D1.** The two horizontal trials (4 and 6) reach a 30 m concentration
ratio of **0.6 or better** against measurement, from 0.37 and 0.39.

**P-D2.** The LFL bracket result stays at **five of six** and the required
factor stays **below 1.25**.

**P-D3.** `dlnh/dlnz` on the four NASA trials rises **above 0.6**, from
0.23 to 0.49. If the depth is now following the rise, this is where it shows.

**P-D4.** The 50 and 100 m arcs, which are currently right on five of six
trials, stay within **0.7 to 1.5**. A change that fixes 30 m by breaking 50 m
has moved the error rather than removed it.

## What would falsify it

If NC3 fails the change is rejected outright, whatever P-D1 does.

If P-D1 passes but P-D4 fails, the cap is redistributing the error and is
rejected.

If P-D1 fails while the negative controls pass, the depth is not what limits
the near-field concentration and the diagnosis in the provenance section is
wrong. Record it and stop.

## RESULTS

*(appended 2026-08-24 after the run; nothing above this line was edited)*

### Negative controls -- **the first run of NC1 and NC2 was invalid**

They were run against an implementation whose frame walk was broken, so the
cap never fired and every case was trivially unchanged. **They reported PASS
because the code did nothing.** The frame walk was fixed afterwards and they
were not re-run until the second registration, where both **FAIL**:

| | criterion | first run (cap inert) | re-run (cap working) |
|---|---|---|---|
| **NC1** LNG pool | < 1 % | 0.000 % -- **invalid** | **36.1 % -- FAIL** |
| **NC2** Prairie Grass | bit-identical | identical -- **invalid** | **FAIL** |
| **NC4** applicability | unchanged | unchanged | unchanged |

**This is the second time in this project that a control passed because the
code under test was not running.** Bug 8 was the same: `vertical_drag`
patched only the submodule, had no effect, and raised no error, so a null
result looked like a clean one.

> **A control that passes has to be shown to have exercised the change.**

The cause of the real failure: **a pool source has a finite depth at the
nozzle and the passive ceiling at small `x` is near zero** -- 0.09 m at 1 m,
against a metres-deep source. The cap crushes the source term. The FFI jets
have a small source and were bitten less, which is why the LH2 results looked
plausible while the dense-gas set was being destroyed.

### The FFI results below were obtained with a working cap and stand as a
### record of what the cap does, but the change is rejected on NC1 and NC2
### before any of them is considered.

### NC3 -- **FAILED**, on three of four

30 m ratio against measurement, downward trials:

| test | before | after | criterion 0.8 to 1.25 |
|---|---|---|---|
| 1 | 0.96 | **0.00** | **FAIL** |
| 3 | 1.04 | **1.96** | **FAIL** |
| 5 | 0.94 | **1.81** | **FAIL** |
| 7 | 1.08 | 1.16 | pass |

**The registration states that an NC3 failure rejects the change outright,
whatever P-D1 does. It is rejected.**

### P-D1 -- half

| test | before | after | criterion >= 0.6 |
|---|---|---|---|
| 4 | 0.39 | **0.69** | pass |
| 6 | 0.37 | **0.37** | **FAIL** |

### P-D4 -- **FAILED**, badly

The 50 and 100 m arcs, which were right on five of six trials, collapse:

| test | 50 m ratio | 100 m ratio |
|---|---|---|
| 1 | **0.00** | **0.00** |
| 3 | 0.38 | 0.03 |
| 4 | 0.43 | 0.14 |
| 5 | 0.26 | 0.01 |
| 6 | **0.00** | **0.00** |
| 7 | 0.45 | 0.27 |

Against a criterion of 0.7 to 1.5. **The change moved the error rather than
removing it**, which the registration also names as a rejection.

### P-D2 -- passed, and it does not save the change

Five of six stay in bracket and the required factor falls from 1.114 to
**1.095**. This is the one criterion the change improves, and on its own it
would have looked like a success. **It is not enough**, and the registration
was written so that it could not be.

### Why it failed -- this is the useful part

**The depth was capped and the rise was not.** The cloud becomes a thin
ribbon that keeps climbing, so it leaves the sensor plane entirely: test 1
reads 0.00 at all three arcs after the change.

The diagnosis that motivated this was that `h` is three times too large at
30 m. That is still true. **What is now also established is that `h` cannot
be corrected on its own**: `docs/27` measured `dlnh/dlnz = 0.23 to 0.49`
against a required 1.0, and capping `h` drives that ratio *further* from 1,
because the cap holds `h` fixed while `z` continues to grow.

> **The depth and the rise are one term, not two.** Any correction has to
> move them together, and this formulation integrates them separately.

### What this rules out

Ninth rejection, and the first to fail *because* it worked on the quantity it
targeted. The near field does respond to the depth -- test 3 goes 6.53 to
12.35 and test 5 goes 7.20 to 13.95, both overshooting -- so the diagnosis is
right about the mechanism. It is the coupling that cannot be had this way.

**Do not retry a depth-only correction.** The next thing to try, if anything,
is a formulation in which `h` is not integrated independently at all but is
set by the rise, and that is a replacement of the depth equation rather than
a module.
