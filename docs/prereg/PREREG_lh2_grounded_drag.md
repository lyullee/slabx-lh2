# Pre-registration: vertical drag on a grounded buoyant cloud

**Registered 2026-08-21, before the branch was written and before any
comparison.** Nothing above the `RESULTS` line is to be edited afterwards.

---

## What was found

`SLAB.FOR` L2929 sets the vertical friction flux to zero whenever the cloud is
grounded:

```fortran
      if(htp .gt. h) then
         ...
         fw = -rhoef*h*wmhs2
      else
         ...
         fw = 0.
      endif
```

and L2505 makes `htp .gt. h` equivalent to `zc .gt. h/2`. Meanwhile L2611
gives a **grounded** cloud that is lighter than air its own accumulating
vertical momentum:

```fortran
               ew = r0*abs(wc0)/(r0*abs(wc0) + abs(sfz))
               wc = ew*(gw + r0*wc0)/r
```

`sfz` is the integral of `fw`, which is zero on that branch. So the rise that
carries the cloud off the ground is generated with **no opposing force at
all**, and only once it has left does drag begin.

Measured on NASA White Sands Test 6 conditions:

| x [m] | z_c [m] | h/2 [m] | grounded? | w_c [m/s] | f_w |
|---|---|---|---|---|---|
| 4.03 | 0.000 | 1.873 | yes | 0.000 | **0** |
| 4.31 | 0.052 | 1.896 | yes | **0.493** | **0** |
| 4.94 | 0.505 | 1.946 | yes | **1.478** | **0** |
| 5.65 | 1.516 | 2.003 | yes | **2.453** | **0** |
| 6.05 | 2.267 | 2.016 | no | 2.934 | active |

The cloud accelerates from rest to 2.45 m/s unopposed, and drag switches on
when it is already moving at 2.9 m/s. Downstream the cloud top reaches
**563 m** against an observed **20 m**, and detachment occurs at **6.2 m**
against an observed **20 m**.

This is Ermak's formulation, verified line by line against the original. It is
not a porting error. It has never been exercised by the validation set because
**none of the thirty-eight field trials has a source lighter than air** — on
the dense branch `wc = -vg*zc/bb`, so the vertical velocity is subordinate to
the cross-wind gravity current and never accumulates on its own.

## The intervention

Apply the same drag on the grounded branch that the original already applies
on the lofted one, whenever the cloud is buoyant and rising:

```python
if not lofted and rho <= rho_a and w_c > 0:
    f_w = -rho_eff * h * c_drag_top * abs(w_c) * w_c
```

The form, the coefficient and the length scale are the ones already in EQ 38.
**No new coefficient is introduced and no existing one is changed.**
`c_drag_top` stays at 0.02.

This is an addition of missing physics rather than an adjustment of a
coefficient — document 06 T12's distinction, where coefficient changes have
been rejected in four of seven attempts and missing-physics additions have
reached a clear conclusion in six of six.

## Predictions

| # | Prediction | Criterion |
|---|---|---|
| **P-G1** | Detachment moves toward the observed distance | NASA Test 6 detachment at **10 - 40 m** (observed ~20 m; currently 6.2 m) |
| **P-G2** | The runaway is bounded | NASA cloud top divided by the observed 20 m falls **below 5.0** (currently 28.2) |
| **P-G3** | FFI is not destroyed by the same change | FFI Test 4 `z_c` at the 100 m arc stays in **1.0 - 3.0 m** (measured peak height 1.8 m; currently ~1.7 - 2.3 m) |
| **P-G4** | The effect scales with buoyancy | the reduction in cloud top is larger for NASA (source `rho/rho_a` 0.79) than for FFI (0.99), by at least **a factor of 3** |
| **NC1** | The dense branch is untouched | the ten LNG pool trials are **bit-identical** |
| **NC2** | A passive cloud is untouched | Prairie Grass conditions are **bit-identical** (`w_c` = 0 throughout) |

**P-G3 is the one that can go wrong quietly.** FFI Test 4 is grounded over its
whole domain (`z_c` 2.5 m against `h/2` 6.2 m at the far end), so it lies
entirely inside the branch being changed. A drag strong enough to stop the
NASA runaway may remove the FFI rise that currently matches the measured peak
height. If P-G1 and P-G2 pass while P-G3 fails, the intervention has traded
one trial for the other and is **not** to be adopted on the strength of the
aggregate.

## What would falsify

**P-G1 above 40 m**: the drag overshoots and the cloud never lifts where it
was observed to. Adopting it would replace an over-rise with an under-rise.

**P-G1 below 10 m with P-G2 passing**: the top is bounded but for the wrong
reason — the cloud is being held down rather than decelerated — and the
mechanism claimed is not the mechanism acting.

**Either negative control failing**: the change has leaked into the dense or
passive limits on which the existing validation rests, and it is a defect
whatever it does for LH2.

## What must not happen

**`c_drag_top` is not to be swept.** The moment a coefficient is tuned to move
the detachment distance onto 20 m, the target stops being independent and
becomes the thing being fitted. Document 18 §18.8 measured the cost of that
route on this very dataset: no coefficient reproduces the orientation
difference at all, fitting the bias to LH2 takes the LNG FAC2 from 0.90 to
0.20, and within LH2 alone the between-trial spread grows from 4.71 to 5.50
as the bias is fitted out.

**The added-mass term stays off.** `PREREG_added_mass` found the
oblate-spheroid `B/h` shape function to be the wrong shape rather than a
mis-scaled one. `c_added_mass` = 0 and is not swept.

**An improved aggregate is not a result.** `PREREG_froude` rejected the Robins
closure although it was better on every aggregate measure, because the
mechanism it was introduced to fix was not fixed. If P-G1 and P-G3 do not both
pass, this is not adopted.

## Scope

One trial for the detachment target, and the target is a reported observation
rather than an instrument reading. **Grade C.** The provenance is second-hand:
the NASA values come from Ichard et al. (ICHS 2009) reading Witcofski &
Chirivella, and NASA TM-83131 has not been obtained.

NC1, NC2 and P-G4 are deterministic and not subject to that limit.

The default stays as Ermak wrote it. Grounded vertical drag is a variant, off
unless asked for.

---

## RESULTS

*(appended 2026-08-21 after the run; nothing above this line was edited)*

### Negative controls, run first

| | bit-identical | max abs difference in `z_c` |
|---|---|---|
| **NC1** LNG pool (Burro 8 deck) | **yes** | 0.000e+00 |
| **NC2** passive SO2 (Prairie Grass) | **yes** | 0.000e+00 |

Both **PASS**. The dense branch takes `wc = -vg*zc/bb` and the passive cloud
has `w_c` = 0, so neither reaches the changed code.

### The intervention does essentially nothing

| | off | on | criterion |
|---|---|---|---|
| **P-G1** NASA detachment [m] | 6.39 | **6.39** | 10 - 40 |
| **P-G2** NASA cloud top / 20 | 36.69 | **36.68** | < 5.0 |
| **P-G3** FFI `z_c` at 100 m [m] | 1.83 | **1.83** | 1.0 - 3.0 |
| **P-G4** top reduction | NASA 1.00x | FFI 1.00x | NASA/FFI >= 3 |

NASA trajectory, `z_c` [m], drag off and on:

| x [m] | 5 | 6 | 8 | 12 | 20 | 40 | 100 | 300 |
|---|---|---|---|---|---|---|---|---|
| off | 0.66 | 1.59 | 7.30 | 18.00 | 50.02 | 117.52 | 246.39 | 425.71 |
| on | 0.66 | 1.58 | 7.28 | 17.95 | 49.95 | 117.39 | 246.25 | 425.54 |

**P-G1 FAIL, P-G2 FAIL, P-G3 PASS but only because nothing moved, P-G4 FAIL.**

### Why

The grounded buoyant window is about 1.3 m long (x = 4.3 to 5.65 m) and the
drag is quadratic in a velocity that is still small there. Over that window
`|Sfz|` reaches roughly 0.4 against `R|w|` of order 260, so `e_w` stays at
0.9985 and the cloud lofts with its momentum intact. Once lofted the original
drag is already active, and it is that drag — not its absence before
lift-off — that fails to bound the rise.

**The missing grounded drag is not the cause.** That explanation is eliminated.

### A correction to how this was being measured ★

The registered definition in `PREREG_lh2_depth` was "cloud top at the arc of
maximum extent". Applied to a model whose rise is unbounded, that picks the
far end of whatever domain is integrated — here **x = 1988 m**, nearly two
kilometres downwind. The NASA observation is of a plume whose downwind extent
was **35 to 40 m**.

Comparing a global maximum at 1988 m against an observation made at 35 - 40 m
is not a comparison. At the distances where the towers actually stood:

| x [m] | slabx `z_c` | slabx top | top / 20 |
|---|---|---|---|
| 9.1 (tower ring 1) | 10.5 | 12.4 | **0.62** |
| 18.3 (ring 2) | 43.2 | 45.2 | **2.26** |
| 33.8 (ring 3) | 97.3 | 99.6 | **4.98** |
| 40.0 (plume extent) | 116.8 | 119.2 | **5.96** |

**The over-prediction at the observation distance is about a factor of five,
not twenty-eight.** The 28.2 reported in `PREREG_lh2_depth` RESULTS followed
the registered definition, and the registered definition was ill-posed. The
verdict there does not change — P-D1 failed either way, and the falsifying
band was 1.5 - 4.0 — but **the number should not be quoted as it stands**, and
document 18 §18.10 and document 21 need the same correction.

### Against Briggs

Bent-over plume rise, `z = (3F x^2 / (2 beta^2 u^3))^(1/3)` with
`beta` = 0.6 and `F` = 95.6 m^4/s^3 from the source state:

| x [m] | Briggs | slabx | observed |
|---|---|---|---|
| 9.1 | 14.6 | **10.5** | ~20 |
| 18.3 | 23.2 | **43.2** | ~20 |
| 33.8 | 35.0 | **97.3** | ~20 |
| 40.0 | 39.1 | **116.8** | ~20 |

Briggs stays within a factor of two of the observation across the whole
range. `slabx` crosses it near 10 m and is 2.8 times Briggs by 34 m.

**The shape is wrong, not only the magnitude.** Briggs gives `z ~ x^(2/3)`;
`slabx` is steeper. A drag term of any strength changes the constant, not the
exponent, which is why the intervention could not have worked and why
sweeping `c_drag_top` would not have worked either.

### Status

| | |
|---|---|
| NC1, NC2 | **PASS** |
| P-G1, P-G2, P-G4 | **FAIL** |
| P-G3 | **PASS, vacuous** |
| adoption | **REJECTED** |

### What is now eliminated

Three explanations for the runaway have been tested and rejected, each with
its own registration:

| | registration | why rejected |
|---|---|---|
| ground reflection hides the lift-off | `PREREG_lh2_liftoff` | reflection removed entirely still gives ground/max 0.88 - 0.99 |
| the cloud is too deep | `PREREG_lh2_depth` | rejected in the opposite direction: the cloud rises too much, not too little |
| vertical drag is missing before lift-off | this one | the window is 1.3 m and contributes 0.15 % of the momentum |

What remains is the **rise law itself**. `slabx` gives an exponent steeper
than the `x^(2/3)` of a bent-over buoyant plume, and no coefficient changes an
exponent. The successor registration is about the form of EQ 6a for a buoyant
cloud, not about any term added to it.

### Reproduction

```bash
cd lh2mod
python3 run_gd.py
```

