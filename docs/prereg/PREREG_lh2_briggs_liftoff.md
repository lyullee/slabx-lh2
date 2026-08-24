# Pre-registration: Briggs' lift-off parameter for buoyant LH2 clouds

**Registered 2026-08-21, before the branch was written and before it was run
on E3.5.** Nothing above the `RESULTS` line is to be edited afterwards.

Runs use the corrected water saturation of document 23 and the plume-width
coupling of `PREREG_lh2_plume_width`, on both arms of every comparison.

---

## What earlier attempts established

`PREREG_lh2_liftoff` tried Hall & Walker's dimensionless buoyancy flux,
`F/(W u^3)` with the mean wind, and thresholds of 0.01 and 0.035. It failed
in a specific way: the group came out at 0.003 - 0.005 on the FFI arcs where
the measurement says a cloud lifted, and reached 0.076 on a dense LNG cloud
that never left the ground. **Below threshold where lift-off happened, above
it where it did not.**

The successor registrations then established, in turn, that the source term of
EQ 6a is a conserved buoyancy flux that no entrainment change can reduce
(`PREREG_lh2_rise_entrainment`), and that the runaway is the absence of a
width-height coupling rather than a missing brake
(`PREREG_lh2_plume_width`, adopted on its discriminating predictions).

## What the literature has that was not being used

Briggs (1973), *Lift-off of buoyant gas initially on the ground*, ATDL
Contribution No. 87. As set out by Hanna (2022) in his EPA review of the
LIFTOFF implementation in AERMOD, of the paper he wrote with Briggs and Chang:

    L_p = g H (rho_a - rho_p) / rho_a / u*^2                         (1)

with `H` the cloud depth and `u*` the friction velocity, whose square is
proportional to the ambient turbulent kinetic energy. Briggs proposed, from
field and laboratory comparisons, that a plume lifts off when

    L_p > 20,   "with an uncertainty of at least a factor of two"

Hanna, Briggs & Chang (1998) then extended it to the grounded case, defining

    F** = F / (U^3 W) = g H (rho_a - rho_p) / (rho_a U^2)            (5)

and fitting, against Hall's wind-tunnel series on broad flat sources, the
ground-level concentration ratio

    C(F** > 0) / C(F** = 0) = exp(-6 F**^0.4)                        (6)

The physical content of (6) is that buoyancy stretches the plume vertically
and thins it at the ground **before** any lift-off, so the effect is
continuous rather than binary. The earlier registration treated it as binary.

**The difference from Hall & Walker is the denominator.** `u*^2` rather than
`U^3`. The friction velocity carries roughness and stability; the mean wind
does not.

EFFECTS took the same route: its 2023 extension (J. Loss Prev. Process Ind.)
cites Briggs' lift-off paper and describes "plume lift-off modelling using an
adapted criterion and the addition of a vertical drag correction", introduced
because heavy-gas models show "too strong plume rise" for lighter-than-air
releases.

## The intervention

Two terms, both taken as published:

1. **Lift-off gate.** Where `L_p > 20`, the ground reflection in the vertical
   concentration profile is released. Between `L_p` = 10 and 20 the reflection
   coefficient is interpolated linearly, the band being Briggs' stated factor
   of two.
2. **Grounded thinning.** Where the cloud is grounded, the ground-level
   concentration is multiplied by `exp(-6 F**^0.4)`.

`u*`, `H`, `rho` and `U` are all already carried by the model. **Free
parameters: zero.** The threshold 20, the coefficient 6 and the exponent 0.4
are Briggs' and Hanna's published values and are not adjusted.

## What has already been seen, and is therefore not a test

`L_p` was evaluated on the six usable FFI trials before this registration was
written. It separated them:

| trial | u* | max L_p | measured at 100 m |
|---|---|---|---|
| 1 | 0.190 | 11.7 | detects |
| 3 | 0.345 | 4.9 | detects |
| 4 | 0.398 | 3.8 | detects |
| 5 | 0.309 | 6.5 | detects |
| **6** | **0.160** | **29.0** | **does not detect** |
| 7 | 0.386 | 2.3 | detects |
| NASA-6 | 0.131 | 558 | detaches at 20 m |

Exactly the two trials the measurement says lifted are the two above 20, and
the separation is 2.5-fold against Briggs' stated factor-of-two uncertainty.
**That is the motivating observation, not evidence.** Everything below is the
test.

## Predictions, on PRESLHY E3.5

E3.5 has not been examined through this parameter. It has measured humidity,
temperature, wind and mass flow on 25 trials, and wind from 0.6 to 4.2 m/s,
so `u*` spans a wider range than FFI's 2.7 to 6.7 m/s.

| # | Prediction | Criterion |
|---|---|---|
| **P-B1** | `L_p` orders the trials by wind, not by release rate | rank correlation of `L_p` against `u10` is **below -0.7**; against mass flow, **between -0.3 and +0.3** |
| **P-B2** | The trials that exceed threshold are the calm ones | every trial with `L_p` > 20 has `u10` **below 2.0 m/s**; no trial above 3.0 m/s exceeds it |
| **P-B3** | It agrees with the independent far-field signature | trials with `L_p` > 20 have a measured 100 m / 30 m arc ratio in the **lowest third** of the set |
| **P-B4** | The grounded correction acts in the observed direction | across the set, `exp(-6 F**^0.4)` correlates with the measured decay ratio at rank correlation **above +0.4** |
| **NC1** | The dense set never reaches it | ten LNG pool trials **bit-identical**; `rho > rho_a` makes the numerator negative |
| **NC2** | The passive limit is untouched | Prairie Grass **bit-identical** |
| **NC3** | FFI's grounded trials do not move much | Tests 3, 4, 5, 7 arc concentrations change by **less than 15 %** |

**P-B1 with P-B2 is the discriminating pair.** The claim is specifically that
`u*` is the right denominator. If `L_p` sorted by release rate instead, the
parameter would be doing what any buoyancy measure does and the choice of
denominator would be unsupported.

## What would falsify

**P-B2 failing with high-wind trials above threshold**: the criterion is
firing where the FFI evidence says clouds stay down.

**P-B1 failing**: `u*` is not carrying the discrimination and the agreement on
FFI was coincidence — six trials is few enough for that.

**P-B3 failing while P-B1 and P-B2 pass**: the parameter is internally
consistent but does not correspond to anything measured.

**Any negative control failing**: the branch has leaked into the limits the
existing validation rests on.

## What must not happen

**The threshold is not to be moved from 20.** Briggs states its uncertainty as
a factor of two, which is why the interpolation band is 10 to 20 — that band
is his stated uncertainty, not a fitted range. If the result needs a threshold
outside 10 - 40, the criterion has failed and is not to be rescued.

**The coefficients in `exp(-6 F**^0.4)` are not to be adjusted.** They are
Briggs' fit to Hall's wind-tunnel data, which is an independent dataset.

**An improved aggregate is not a result.** `PREREG_froude` rejected the Robins
closure although it was better on every aggregate measure. If P-B1 and P-B2 do
not both pass, this is not adopted.

## Scope

E3.5's far-field sensors saturate at 4 vol% and its stand geometry requires
the wind-axis rotation of document 22 §22.11, so P-B3 rests on the arc decay
ratio rather than on absolute concentrations. **Grade C.** P-B1, P-B2, NC1 and
NC2 are deterministic.

The default stays as Ermak wrote it. Lift-off is a variant, off unless asked
for.

---

## RESULTS

*(appended 2026-08-21 after the run; nothing above this line was edited)*

### Negative controls, run first

| | max `L_p` | fires? |
|---|---|---|
| **NC1** LNG pool (Burro 8 deck) | **0.443** | no — 45x below the band |
| **NC2** passive SO2 (Prairie Grass) | **0.000** | no |

Both **PASS**. On a dense cloud the numerator is negative and clamps to zero;
on a passive cloud it is zero exactly.

### E3.5, seventeen usable trials

| trial | u10 | q [g/s] | u* | max `L_p` | `F**` | `exp(-6F**^0.4)` | measured outer/inner |
|---|---|---|---|---|---|---|---|
| 20 | **0.57** | 105.5 | 0.046 | **226.9** | 1.648 | 0.001 | 0.754 |
| 13 | **1.50** | 265.0 | 0.123 | **102.6** | 1.271 | 0.001 | 0.964 |
| 4 | 1.83 | 105.5 | 0.150 | **33.3** | 0.301 | 0.024 | 0.944 |
| 22 | 1.70 | 298.0 | 0.139 | **31.3** | 0.229 | 0.036 | 1.010 |
| 19 | 1.60 | 139.5 | 0.131 | **29.7** | 0.255 | 0.031 | 0.644 |
| 8 | 2.37 | 105.5 | 0.194 | **22.8** | 0.312 | 0.023 | 0.556 |
| 7 | 2.50 | 105.5 | 0.205 | **22.6** | 0.311 | 0.023 | 0.847 |
| 23 | 1.70 | 265.0 | 0.139 | **22.3** | 0.179 | 0.049 | 1.000 |
| 14 | 1.93 | 265.0 | 0.158 | **20.4** | 0.173 | 0.051 | 0.000 |
| 10 | 2.47 | 298.0 | 0.202 | 18.1 | 0.143 | 0.063 | 1.000 |
| 24 | 1.90 | 95.0 | 0.156 | 9.3 | 0.084 | 0.108 | 0.675 |
| 11 | 2.70 | 265.0 | 0.221 | 9.1 | 0.082 | 0.110 | 1.000 |
| 3 | 3.60 | 139.5 | 0.295 | 9.0 | 0.089 | 0.102 | 0.973 |
| 6 | 3.90 | 105.5 | 0.319 | 5.2 | 0.054 | 0.154 | 1.165 |
| 17 | 2.87 | 105.5 | 0.235 | 5.0 | 0.042 | 0.186 | 0.422 |
| 12 | 2.70 | 95.0 | 0.221 | 4.6 | 0.055 | 0.153 | 0.910 |
| 16 | **4.17** | 139.5 | 0.341 | **2.4** | 0.022 | 0.269 | 0.678 |

### P-B1 — PASSED, both parts

| | value | criterion |
|---|---|---|
| rank correlation of `L_p` with `u10` | **-0.891** | below -0.70 |
| rank correlation of `L_p` with mass flow | **+0.213** | between -0.30 and +0.30 |

**`L_p` sorts by wind and not by release rate.** Trial 20 at 0.57 m/s and
105 g/s ranks above trial 22 at 1.70 m/s and 298 g/s, which is nearly three
times the flow. That is the structural claim about `u*` being the right
denominator, and it holds on a set that was not used to motivate it.

### P-B2 — FAILED, narrowly

Nine trials exceed the threshold: 4, 7, 8, 13, 14, 19, 20, 22, 23. Their wind
speeds are 1.83, 2.50, 2.37, 1.50, 1.93, 1.60, 0.57, 1.70, 1.70 m/s.

The criterion was that **every** one be below 2.0 m/s. **Trials 7 and 2.50 and
8 at 2.37 exceed it.** Seven of nine comply.

The second half passes: **no trial above 3.0 m/s exceeds the threshold**, and
the two calmest trials in the set are the two highest `L_p` by a wide margin.

Trials 7 and 8 are the two vertical-downward releases modelled as an
evaporating pool of the observed 0.7 m radius. A low-momentum pool gives a
deeper cloud, and `L_p` is linear in depth. **The two exceedances are the two
trials whose source model differs from the rest**, which is a property of the
source treatment rather than of the criterion, but the prediction as written
did not allow for it and is recorded as failed.

### P-B3 — FAILED

Lowest third of the measured outer/inner ratio: trials 8, 14, 17, 19, 24.
Trials above threshold: 4, 7, 8, 13, 14, 19, 20, 22, 23. The overlap is 8, 14
and 19 — three of five. Trials 17 and 24 are in the lowest third and do not
fire; trials 4, 13, 20, 22, 23 fire and are not.

### P-B4 — FAILED

Rank correlation of `exp(-6 F**^0.4)` with the measured ratio: **+0.071**,
against a criterion of +0.40.

### The target of P-B3 and P-B4 is censored

Counting sensors at or above the 3.90 %vol over-range ceiling:

| trial | inner max | outer max | ratio | saturated sensors |
|---|---|---|---|---|
| 10 | 4.00 | 4.00 | **1.000** | **10** |
| 11 | 4.00 | 4.00 | **1.000** | **12** |
| 23 | 4.00 | 4.00 | **1.000** | **9** |
| 22 | 3.96 | 4.00 | 1.010 | 6 |
| 15 | 4.00 | 3.90 | 0.975 | 5 |
| 14 | **0.04** | **0.00** | **0.000** | 0 |

**Four trials return a ratio of exactly 1.000 or 1.010 because both arcs sit
on the instrument ceiling**, and trial 14 returns 0.000 because it detected
essentially nothing anywhere. Neither carries information about decay.

This is a property of the dataset established in document 22 §22.11 before
this registration was written, and using the ratio as a target anyway was an
error in the registration rather than a finding about the criterion. **P-B3
and P-B4 are recorded as failed, and as uninformative.**

### Status

| | |
|---|---|
| NC1, NC2 | **PASS** |
| **P-B1** rank ordering by wind, not rate | **PASS**, both parts |
| **P-B2** all firing trials below 2.0 m/s | **FAIL** — 7 of 9; the two exceptions are the two pool-source trials |
| P-B3, P-B4 | **FAIL**, on a censored target |
| **adoption** | **NOT ADOPTED** — the registration requires P-B1 and P-B2 both to pass |

### What this establishes

**The denominator is right.** `L_p` orders seventeen trials by wind speed at a
rank correlation of -0.891 and shows no ordering by release rate. That is the
claim that distinguishes Briggs' parameter from the one tried in
`PREREG_lh2_liftoff`, and it is confirmed on a set that played no part in
motivating it.

**The threshold is close but not clean.** Nine trials exceed 20, and the
firing set runs to 2.50 m/s rather than stopping at 2.0. Briggs states the
threshold's uncertainty as a factor of two, so 2.50 m/s is comfortably inside
his own stated band -- but the registration fixed 2.0 before the run and it
was missed.

**The far-field decay ratio cannot be used as a target on E3.5.** Four of
seventeen trials are pinned at the instrument ceiling on both arcs.

### What a successor needs

Not a different criterion. A target that is not censored:

- **FFI**, where `L_p` separated six trials cleanly at 2.5-fold, but which
  motivated this registration and cannot now test it
- **RR986**, four trials, thirty sensors at six heights from 0.25 to 2.7 m,
  concentrations not yet extracted, and `u` from 1.4 to 4.0 m/s at a fixed
  60 L/min -- **wind varied at constant source**, which is what P-B1 and P-B2
  need and what no other dataset offers
- **NASA Test 6**, where the detachment distance of about 20 m is a length
  rather than a concentration

**RR986 is the one to use.** It is the only set that varies wind at a fixed
release rate, and it has not been opened.

### Reproduction

```bash
cd lh2mod
python3 briggs.py        # the parameter on FFI and NASA
python3 run_briggs.py    # the registered predictions on E3.5
```


---

## ADDENDUM — a second registered test, on NASA

*(registered 2026-08-21 after the E3.5 results above, before the model was run
on these conditions. The observation was read from Witcofski & Chirivella
(1984) Tables 1 and 4; the model's answer is unseen.)*

The E3.5 test failed P-B2 on a target that was censored and on two trials
whose source model differed from the rest. The original NASA paper, obtained
after that run, carries what neither FFI nor E3.5 nor RR986 could give at
once: **a fixed spill quantity, wind varied by a factor of four, and a
far-field measurement of how high the flammable cloud sat.**

Witcofski & Chirivella (1984), Table 1 and Table 4. Spill 5.7 m^3 into a 9.1 m
pond; towers 7, 8 and 9 at 33.8 to 36.6 m:

| test | wind [m/s] | spill time [s] | rate [kg/s] | **minimum height of flammable cloud [m]** |
|---|---|---|---|---|
| 2 | 1.6 | 40 | 10.1 | **18.3** |
| 6 | 2.2 | 35 | 11.5 | **3.4** |
| 4 | 3.6 | 33 | 12.2 | **6.4** |
| 5 | 6.3 | 24 | 16.8 | **0.3** |

Rank correlation of the measured minimum height against wind: **-0.80**.

Note the rate runs the *other* way: the windiest test has the largest rate.
So a criterion that sorted by rate would put Test 5 highest, and the
measurement puts it lowest. **The two candidate orderings are opposed here**,
which is what E3.5 could not offer.

| # | Prediction | Criterion |
|---|---|---|
| **P-N1** | `L_p` orders these four by wind, against the opposing rate ordering | rank correlation of `L_p` with wind **at or below -0.80**; with rate, **above -0.40** |
| **P-N2** | The calmest test is the one that lifts | Test 2 has the **highest** `L_p` of the four, and Test 5 the **lowest** |
| **P-N3** | The model puts the flammable cloud higher when the wind is lighter | the lowest height at which the model reaches 4 vol% at 33.8 m ranks with wind at **-0.60 or below** |
| **P-N4** | The threshold lands between the tests the measurement separates | Test 2 exceeds `L_p` = 20; Test 5 does not |

**P-N1 is the discriminating one**, because wind and rate are anti-correlated
across these four trials and only one of them can be producing the ordering.

Falsified if `L_p` sorts by rate, or if Test 5 exceeds the threshold while
Test 2 does not.

Nothing is adjusted. Threshold 20, ambient roughness 3 mm as reported, wind at
10 m, pond radius 4.55 m as built.

### RESULTS — NASA addendum

*(appended 2026-08-21 after the run; nothing above was edited)*

| test | u | rate [kg/s] | u* | **max `L_p`** | model lowest 4 vol% height at 33.8 m | measured |
|---|---|---|---|---|---|---|
| 2 | 1.6 | 10.09 | 0.081 | **1855.5** | never reaches 4 % | **18.3 m** |
| 6 | 2.2 | 11.53 | 0.111 | **751.2** | never reaches 4 % | **3.4 m** |
| 4 | 3.6 | 12.23 | 0.182 | **206.7** | 27.0 m | **6.4 m** |
| 5 | 6.3 | 16.82 | 0.319 | **55.6** | 11.1 m | **0.3 m** |

**P-N1, first half — PASSED.** Rank correlation of `L_p` with wind: **-1.000**,
against a criterion of -0.80. Perfect ordering.

**P-N1, second half — MIS-SPECIFIED.** The criterion was that `L_p` correlate
with rate above -0.40; it comes out at -1.000. But wind and rate are
**perfectly positively correlated across these four trials** (1.6, 2.2, 3.6,
6.3 m/s against 10.1, 11.5, 12.2, 16.8 kg/s), so any quantity that
anti-correlates with wind must anti-correlate with rate. The criterion cannot
be met by any wind-sorted variable and was impossible as written.

The registration claimed "the two candidate orderings are opposed here". That
was the wrong way round: they are collinear. What the data does establish is
weaker but still useful — a criterion driven by release rate would rank Test 5
**highest**, and the measurement puts its flammable cloud lowest of the four,
at 0.3 m. `L_p` ranks Test 5 lowest. **A rate-driven measure would have the
sign backwards; `L_p` does not.**

**P-N2 — PASSED.** Highest `L_p` is Test 2, lowest is Test 5, exactly as
registered.

**P-N3 — FAILED.** The model's lowest flammable height ranks with wind at
**+0.800**, against a criterion of -0.60 — the wrong sign. And on the two
calmest trials the model never reaches 4 vol% at 33.8 m at any height between
0.3 and 40 m, while the measurement found flammable cloud at 18.3 and 3.4 m.
Where it does reach it, it is far too high: 27.0 m against 6.4, and 11.1
against 0.3.

**This is the over-rise, unchanged.** The plume-width coupling was enabled and
did not repair it at this scale.

**P-N4 — FAILED.** Test 2 exceeds the threshold as required, but so does Test
5, at **55.6** against a required 20 or below. **All four NASA trials exceed
the threshold**, including the one whose flammable cloud sat at ground level.

### What the four datasets together show

| dataset | source | wind range | `L_p` ordering | threshold 20 separates? |
|---|---|---|---|---|
| FFI | 0.16 - 0.83 kg/s | 2.7 - 6.7 | correct | **yes**, 29.0 against 2.3 - 11.7 |
| E3.5 | 0.095 - 0.30 kg/s | 0.6 - 4.2 | correct, rho_s = -0.891 | mostly, 7 of 9 below 2.0 m/s |
| RR986 | 0.0708 kg/s fixed | 1.4 - 4.0 | correct, 52.5 to 3.8 monotone | **yes**, transition at 2.7 - 2.9 m/s |
| **NASA** | **10 - 17 kg/s** | 1.6 - 6.3 | **correct, rho_s = -1.000** | **no — all four exceed it** |

**`L_p` orders every dataset correctly and the threshold of 20 does not
transfer across scale.** The three sets where it separates span 0.07 to
0.83 kg/s; NASA is twenty to two hundred times larger and every trial clears
the threshold by a factor of three to ninety.

That is a coherent statement about what the parameter is: a good **ordering**
variable within a scale, and not an absolute threshold across scales. Briggs
gives the uncertainty as a factor of two; the spread here is a factor of
ninety.

### Status of the whole registration

| | |
|---|---|
| NC1, NC2 | **PASS** |
| P-B1 (E3.5, ordering) | **PASS** |
| P-B2 (E3.5, threshold) | **FAIL**, 7 of 9 |
| P-B3, P-B4 | **FAIL**, censored target |
| P-N1 first half (NASA, ordering) | **PASS**, -1.000 |
| P-N1 second half | **mis-specified**, unfalsifiable |
| P-N2 | **PASS** |
| P-N3 (model height) | **FAIL**, wrong sign, over-rise unchanged |
| P-N4 (NASA, threshold) | **FAIL**, all four exceed |
| **adoption** | **NOT ADOPTED** |

**Ordering: four of four datasets. Threshold: three of four, failing at the
largest scale.** The parameter is not adopted as a gate. It is worth carrying
as a diagnostic, reported rather than acted on, in the same way `w_c/u` is.

### One correction to the record

Documents 20 and 22 state that NASA Test 6 detached "about 20 m downwind,
20.93 s after the start", cited from Ichard et al. (ICHS 2009). The original
paper gives that number differently: its Figures 7 and 8 are concentration
contours at 20.94 and 21.33 s spanning 0 to 40 m downwind, and Ichard read
detachment off those. Witcofski & Chirivella's own statement from the
photographs is **ground-level cloud travel of 50 to 100 m**, and for one test
"the visible cloud was observed to remain on the ground for about 65 m in the
downwind direction and then began to rise at about a 30 degree angle and at a
vertical speed of about 1 m/s".

**Those are two different measurements** -- a concentration contour and the
visible cloud edge, which the paper places at 8 to 9 vol%. Document 20 §20.1
and document 22 should carry both, attributed separately.

### Reproduction

```bash
cd lh2mod
python3 nasa4.py
```

