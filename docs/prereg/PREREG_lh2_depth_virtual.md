# PREREG — a depth ceiling measured from a virtual origin

**Registered 2026-08-24, before implementation.** Nothing above the `RESULTS`
line is to be edited afterwards.

## What the two rejected attempts established

`PREREG_lh2_depth_cap` and `PREREG_lh2_depth_plume` both put the passive
ceiling at `k sigma_z(x)` with `x` measured from the source. That fails on the
dense-gas controls for a reason that is now understood:

| x | `1.5 sigma_z(x)` |
|---|---|
| 1 m | **0.09 m** |
| 10 m | 0.90 m |

**A pool source is metres deep at `x = 0`.** The ceiling crushes it in the
first step; LNG moved 36 % and Prairie Grass was no longer bit-identical.
`sigma_z(x)` goes to zero at the source and a real cloud does not.

The diagnosis they were built on is unaffected: at 30 m the FFI test 6 cloud
is 8.1 m wide and 7.8 m deep against a passive layer of 7.2 m and 2.6 m --
**the width is right to 10 % and the depth is three times too large.**

## The change

The ceiling is measured from a **virtual origin** placed so that it equals the
cloud's own depth where the cloud begins:

    h <= k * sigma_z(x + x_v),     x_v such that  k sigma_z(x_v) = h_0

with `h_0` the depth at the first step and `k = 1.5` as before. `x_v` is
solved once per run from the source state; **it is not a fitted parameter but
a consequence of `h_0`**, and a source that is already deeper than any passive
layer gets an `x_v` large enough that the ceiling never binds.

This is the standard virtual-source construction: a plume that starts with a
finite size is treated as one that began upstream with zero size.

The lofted branch is carried over unchanged from `PREREG_lh2_depth_plume`:
once the cloud is buoyant and rising, `dh/dx >= 2 beta w_c / u`, the
Morton-Taylor-Turner `b = beta z`. **It was never reached in that run and is
still untested.**

## Negative controls -- run FIRST, and each must be shown to have fired

**NC0.** `depth_cap.fired_count()` after each control run is reported. **A
control that passes with zero firings has tested nothing** and is not a pass.
This exists because NC1 and NC2 of the first registration passed against a
patch whose frame walk was broken.

**NC1.** Ten LNG pool trials: change **below 1 %**.

**NC2.** Prairie Grass passive: **bit-identical**.

**NC3.** The four downward FFI trials at 30 m: **every ratio within 0.8 to
1.25** (now 0.94 to 1.17).

**NC4.** All six trials at 50 and 100 m: **within 0.7 to 1.5**.

**NC5.** No trial changes its applicability status.

## Predictions

**P-V1.** The two horizontal trials reach a 30 m ratio of **0.6 or better**
(now 0.37 and 0.39).

**P-V2.** `dlnh/dlnz` on the four NASA trials rises **above 0.7** (now 0.23 to
0.49). **The discriminating prediction**, and the one registered before any of
this work.

**P-V3.** The NASA rise exponent falls **below 0.95** on at least three of
four (now 1.05 to 1.28).

**P-V4.** The LFL bracket stays at **five of six** and the required factor
stays **below 1.25**.

## What would falsify it

Any negative-control failure rejects it.

**If P-V1 passes and P-V2 fails**, the near field has been fixed without the
coupling and the change is a fit. Reject it.

If P-V1 and P-V2 both fail while the controls pass, the virtual origin has
made the ceiling inert and the approach is exhausted. Record it and stop.

## RESULTS

*(appended 2026-08-24; nothing above the amendment was edited)*

### Negative controls -- **FAILED**. Rejected, and no further amendment.

| version | LNG worst | ceiling firings | NC2 |
|---|---|---|---|
| class D only, `k = 1.5` | **36.1 %** | 742 | fail |
| all six classes, `k = 1.5` | **1.33 %** | 297 | fail |
| all six classes, **`k = 1.09`** | **17.2 %** | 621 | fail |

The predictions were not evaluated.

### The premise is false

Lowering `k` from the asserted 1.5 to the model's own measured passive limit
of 1.09 made it **worse**, not better: the ceiling bound harder and LNG moved
further. That is the opposite of what a correct ceiling does.

The registration rests on the claim that

> a layer cannot be thicker than the turbulence can mix it

and **that is not true near a source.** A dense-gas cloud has gravity-driven
spreading and source shear of its own, and it is legitimately deeper than a
passively dispersing layer at the same distance. Constraining it to the
passive limit removes physics the model is right to have.

The best version reached 1.33 %, above the registered 1 % and five times the
0.25 % that the dense-gas set moves under any accepted change here. **It was
never close.**

### What was learned, and it is not nothing

**`k` is 1.09, not 1.5.** SLAB's own passive asymptote was measured on the way
past: `h / sigma_z` is 1.87 at 10 m, 1.20 at 100 m and 1.09 from 300 m out.
That is a property of the formulation nobody had written down, and it is what
the depth converges to when nothing else is acting.

**The stability class matters and the first version ignored it.** Applying the
D curve to class C and E releases moved LNG by 36 %; using the right curve for
each cut that to 1.33 %. Any future work that reaches for `sigma_z` must take
the class from the atmosphere.

**A ceiling is the wrong shape of correction.** The depth is three times too
large at 30 m on a horizontal LH2 jet -- that stands -- but it is too large
because of what the entrainment closure does, not because it has been allowed
past a limit. Removing the excess requires changing what produces it.

### Three registrations, one conclusion

`PREREG_lh2_depth_cap`, `PREREG_lh2_depth_plume` and this one all attempted to
bound the depth from outside. **The approach is exhausted.** The lofted
branch, `dh/dx >= 2 beta w_c / u`, was never reached in any of the three and
remains untested; if it is tried, it must be as a replacement for the depth
equation rather than as a floor under a ceiling.

---

## AMENDMENT 1 — two defects in the specification, found by the controls

*(appended 2026-08-24, before the predictions were evaluated)*

The controls were run first as registered and both failed. The failures are in
the specification, not in the hypothesis, and both are corrected here with the
reasoning stated **before** the corrected version is run.

### Defect 1 — one stability class for six

The registration specified the class D `sigma_z` curve "because the trials are
all class D". **The negative controls are not**: the LNG set contains class C
and E releases, and applying the D curve to them put the ceiling in the wrong
place. LNG moved 36 %.

Corrected to the Briggs open-country family, all six classes, taken from the
`atmosphere` object. Published coefficients, nothing fitted. LNG fell to
**1.33 %**, still above the 1 % criterion.

### Defect 2 — `k` was asserted, not measured

`k = 1.5` was stated as "the standard top-hat conversion". **SLAB's own
passive limit disagrees.** Running the Prairie Grass release and comparing the
depth against the Briggs curve:

| x [m] | `h / sigma_z` |
|---|---|
| 10 | 1.87 |
| 50 | 1.33 |
| 100 | 1.20 |
| 300 | 1.09 |
| 600 | **1.09** |

**The model's own passive asymptote is 1.09.** A ceiling at 1.5 is above what
the model produces for a passive plume, so it binds nowhere it should and the
comparison is not against the model's own physics.

`k` is set to **1.09**, measured from the model's passive limit rather than
asserted. **It is not fitted to any control or prediction outcome** -- it is
read from a run that contains no LH2 and no cap.

### Defect 3 — the origin is placed from a zero depth

The trajectory begins with `h = 0` at a negative `x`, so `virtual_origin(0)`
returns 0 and the origin lands half a metre upwind. The ceiling then binds in
the first few metres where the source still has its own size.

The origin is instead placed at the first step where the depth is finite.

### What is unchanged

The hypothesis, every negative control and every prediction above. The lofted
branch is untouched and still untested.

**If the corrected version fails a control, the approach is rejected and no
further amendment will be made.**
