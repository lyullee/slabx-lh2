# Pre-registration: buoyancy-driven entrainment on a rising cloud

**Registered 2026-08-21, before the term was written and before any
comparison.** Nothing above the `RESULTS` line is to be edited afterwards.

---

## What was found

SLAB carries the driver of buoyant rise and none of the brakes.

| brake | state in `slabx` |
|---|---|
| added mass | `c_added_mass` = 0; the oblate-spheroid shape function was rejected by `PREREG_added_mass` P-AM7 |
| entrainment that responds to the rise | **absent** — `w_c` appears nowhere in `entrainment()`, only inside `drag(cl.w_c)` |
| vertical friction while grounded | `fw = 0` on that branch, verified against `SLAB.FOR` L2929 |
| ground attachment | a single `z_c > h/2` switch |

The consequence is measured in `PREREG_lh2_depth`: on NASA White Sands Test 6
the predicted cloud top is 99.6 m at the 33.8 m tower ring against an observed
plume extent of about 20 m, a factor of **4.98**, and the rise does not turn
over.

The mechanism is measured in document 22 §22.3. The source term of EQ 6a is
`dGw/dx = -g (rho - rho_a) B h`. Between 6 m and 561 m the density deficit
falls by **436x** while `B h` grows by **37x**, so the term itself falls by
only **12x**. The cloud's growing footprint compensates for its vanishing
density deficit, `Gw` keeps accumulating, and `w_c` stays positive.

**Nothing in the model couples the entrainment to the rise**, so there is no
feedback by which rising dilutes the cloud faster and removes its own driver.

## The intervention

HyRAM+ 6.1 carries exactly that feedback. Its entrainment is

```python
Fr_L   = V_cl**2 * rho_cl / (g * B * abs(rho_amb - rho_cl))
E_buoy = alpha_buoy / Fr_L * (2*pi*V_cl*B) * sin(theta)
E      = E_mom + E_buoy                      # capped at alpha = 0.082
```

so the entrainment **velocity** contributed is
`alpha_buoy / Fr_L * V_cl * sin(theta)`. As the plume turns upward,
`sin(theta)` grows, entrainment grows, the cloud dilutes faster, the density
deficit falls faster, and the rise limits itself.

Ported into `slabx` without touching the integrator, because `slabx` already
carries `w_c` and `u`, so the angle is available without making it a state
variable:

```python
V     = hypot(u, w_c)
sin_t = w_c / V                             # zero unless the cloud is rising
Fr_L  = V**2 * rho / (g * h * abs(rho_a - rho))
W_buoy = alpha_buoy / Fr_L * V * sin_t
W_e   = min(W_e + W_buoy, alpha_cap * V)
```

applied only when `w_c > 0`.

**Declared choices, made before the run:**

- **`alpha_buoy` = 0.28 and `alpha_cap` = 0.082**, the published Houf & Schefer
  values that HyRAM+ uses. **No new coefficient is introduced and no existing
  one is changed.**
- **The length in `Fr_L` is the cloud depth `h`**, not the half-width. HyRAM's
  plume is axisymmetric and has one radius; a slab has two lengths, and the
  term is being added to the *vertical* entrainment, so the vertical scale is
  the consistent choice. This is a modelling decision, not a fitted one, and
  it is recorded here because it could have gone the other way.
- `slabx` stores reduced velocities (`W_e = sqrt3 * w`), so the term is added
  as `w += W_buoy / sqrt3` to make the added `W_e` equal `W_buoy`.

## Predictions

| # | Prediction | Criterion |
|---|---|---|
| **P-E1** | The rise is bounded at the distance where it was observed | NASA cloud top at the **33.8 m** tower ring within a factor of **2** of the observed 20 m; currently 4.98 |
| **P-E2** | The buoyancy source term decays with the deficit that feeds it | over 6 to 561 m, (deficit decay) / (`dGw/dx` decay) falls **below 5**; currently 436/12 = **36** |
| **P-E3** | The term acts where the angle is large and nowhere else | the fractional change in max `w_c/u` is at least **10x** larger for NASA (max `w_c/u` = 3.68) than for FFI Test 4 (0.03) |
| **NC1** | The dense limit is untouched | the ten LNG pool trials are **bit-identical** — `z_c` = 0 throughout, so `sin(theta)` = 0 |
| **NC2** | The passive limit is untouched | Prairie Grass conditions **bit-identical** |
| **NC3** | The trials that are inside the premise barely move | FFI Tests 1, 3, 4, 7 arc concentrations change by **< 10 %** |

**P-E3 and NC3 are the discriminating pair.** Every intervention tried so far
either did nothing everywhere or would have moved everything. This one has a
dose-response built in: `sin(theta)` is 0.03 on FFI and 0.97 on NASA, so the
same term must act thirty times harder on one than the other. If it moves both
or neither, the mechanism claimed is not the mechanism acting.

## What would falsify

**P-E1 passing while NC3 fails**: the rise has been bounded by diluting
everything, not by the angle-dependent feedback. Not adopted.

**P-E2 failing while P-E1 passes**: the cloud top has come down without the
source term decaying, so something else changed. Not adopted.

**Any negative control failing**: the term has leaked into the dense or passive
limits that the existing validation rests on.

**P-E1 giving a factor below 0.5**: the feedback overshoots and the cloud no
longer rises where it was observed to. Replacing an over-rise with an
under-rise is not an improvement.

## What must not happen

**`alpha_buoy` is not to be swept.** It is 0.28 as published. The moment it is
tuned to put the cloud top on 20 m, the target stops being independent.
Document 18 §18.8 measured what that route costs on this dataset: no
coefficient reproduces the orientation difference at all, fitting the bias to
LH2 takes the LNG FAC2 from 0.90 to 0.20, and within LH2 alone the
between-trial spread grows from 4.71 to 5.50 as the bias is fitted out.

**The length scale in `Fr_L` is not to be switched to `b_half` after seeing
the result.** It is declared above as `h`. If `h` fails, that is the result.

**Added mass stays off.** `c_added_mass` = 0, not swept.

**An improved aggregate is not a result.** `PREREG_froude` rejected the Robins
closure although it was better on every aggregate measure, because the
mechanism it was introduced to fix was not fixed. If P-E1 and P-E3 do not both
pass, this is not adopted.

## What this does not claim

It does not repair the premise. Document 22 establishes that `slabx` marches in
`x`, which presumes downwind advection, and that `w_c/u` reaches 3.68 on NASA
Test 6. **If this term succeeds it will be because it lowers `w_c/u` back into
the range where the premise holds — which is a consequence, not a
justification.** The applicability statement of document 22 §22.10 stands
either way, and the successful case must still be reported as a model run
outside its own premise.

## Scope

One trial carries the target. The target is a reported plume extent, and the
provenance is second-hand: the NASA numbers come from Ichard et al. (ICHS 2009)
reading Witcofski & Chirivella, and NASA TM-83131 has not been obtained.
**Grade C.** NC1, NC2 and P-E3 are deterministic.

The default stays as Ermak wrote it. Rise entrainment is a variant, off unless
asked for.

---

## RESULTS

*(appended 2026-08-21 after the run; nothing above this line was edited)*

### Negative controls, run first

| | bit-identical | max abs difference in `z_c` |
|---|---|---|
| **NC1** LNG pool (Burro 8 deck) | **yes** | 0.000e+00 |
| **NC2** passive SO2 (Prairie Grass) | **yes** | 0.000e+00 |

Both **PASS**. `z_c` is zero on the dense grounded branch and `w_c` is zero for
a passive cloud, so the gate on `w_c > 0` holds.

### P-E1 — FAILED

| NASA cloud top at the 33.8 m ring | off | on |
|---|---|---|
| height [m] | 99.56 | **82.76** |
| vs observed 20 m | 4.98x | **4.14x** |

Criterion was within a factor of 2. The rise came down by **17 %**, in the
right direction and nowhere near far enough.

### P-E2 — FAILED, and moved the wrong way

Over 6 to 561 m:

| | deficit decay | `dGw/dx` decay | ratio |
|---|---|---|---|
| off | 434x | 11.9x | **36.5** |
| on | **582x** | 12.9x | **45.0** |

Criterion was below 5. **It got worse.** More entrainment made the density
deficit fall 34 % faster, and the buoyancy source term fall only 8 % faster.

### P-E3 — FAILED

| | max `w_c/u` off | on | change |
|---|---|---|---|
| NASA Test 6 | 3.675 | 3.082 | **16.1 %** |
| FFI Test 4 | 0.030 | 0.031 | **3.7 %** |
| ratio | | | **4.33** |

Criterion was 10. The dose-response is there and it is real, but it is a
factor of four rather than the thirty that `sin(theta)` implies.

### NC3 — FAILED

FFI arc concentrations, z = 1 m:

| test | arc [m] | off [%vol] | on [%vol] | change |
|---|---|---|---|---|
| 1 | 50 | 2.3830 | 2.7165 | **14.00 %** |
| 7 | 30 | 2.9535 | 3.3146 | 12.22 % |
| 7 | 50 | 1.2910 | 1.4870 | **15.18 %** |
| 4 | 30 | 6.1412 | 6.4946 | 5.75 % |
| 3 | 100 | 1.2161 | 1.2513 | 2.90 % |

Criterion was below 10 %; the worst is **15.18 %**, on the two smallest
releases. The term is not as confined to the large-angle case as `sin(theta)`
alone suggests, because `Fr_L` is small near the source where the cloud is
cold and shallow, and that is where it acts on the FFI trials.

### Status

| | |
|---|---|
| NC1, NC2 | **PASS** |
| P-E1, P-E2, P-E3, NC3 | **FAIL** |
| adoption | **REJECTED** |

### Why entrainment cannot be the brake ★

P-E2 moving the wrong way is the informative result, and it has an algebraic
explanation.

The source term is `dGw/dx = g (rho_a - rho) B h`. For a dilute cloud the
density deficit scales with the released mass fraction, `rho_a - rho ~ rho_a m`,
and `m = q / R` while `R = rho u B h`. So

    (rho_a - rho) B h  ~  rho_a (q/R) (R / rho u)  =  rho_a q / (rho u)

**The source term is the conserved buoyancy flux divided by the wind speed. It
does not contain `R`.** Entraining more air lowers the deficit and raises `B h`
in nearly the same proportion, and the product barely moves. That is not a
defect: buoyancy flux *is* conserved in a plume, and the model is right to
carry it that way.

Measured: entrainment roughly doubled, the deficit decayed 34 % faster, and
the source term decayed 8 % faster.

So the brake cannot act on the buoyancy production. It has to act on the other
side of `w_c = Gw / R` — either by growing `R` far faster than any entrainment
closure of this form does, or by adding effective mass that `R` does not
count.

**A rising plume's `R` grows as `z^2`, which is what produces Briggs's
`z ~ x^(2/3)`.** Document 22 §22.9 measured `slabx`'s cloud at 13 times
narrower than `beta z` at the far field: it rises to hundreds of metres while
entraining like a ground-level slab. Doubling the entrainment velocity does not
change that scaling; only coupling the width to the height would, and that is
the arclength reformulation, not a term.

### What this leaves

Three brakes were listed in the registration. Two are now closed:

| brake | status |
|---|---|
| vertical friction while grounded | rejected, `PREREG_lh2_grounded_drag` |
| entrainment that responds to the rise | **rejected here** |
| added mass | **open** |
| ground attachment | not attempted |

**Added mass is the only one left that acts where the algebra says a brake must
act** — it multiplies the effective mass in `w_c = Gw / R` rather than trying
to reduce `Gw`. `PREREG_added_mass` rejected the oblate-spheroid `B/h` shape
function as structurally wrong rather than mis-scaled, and explicitly left the
term itself open. On NASA Test 6 the cloud is 30 m wide and 4 m deep at the
point it lifts, `B/h` near 7.5, which is the flat-disc limit where added mass
is largest and where Hall & Walker measured the strongest suppression of rise.

That is the next registration, and it is a different hypothesis from P-AM7, not
a re-run of it: P-AM7 tested whether a coefficient could fit a series of
widths, and failed. This would test whether the term, with a shape function
taken from potential flow rather than from the oblate spheroid, bounds a rise
that is otherwise unbounded.

### Reproduction

```bash
cd lh2mod
python3 run_re.py
```

