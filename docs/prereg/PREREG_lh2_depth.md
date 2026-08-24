# Pre-registration: is the vertical extent of a buoyant LH2 cloud over-predicted?

**Registered 2026-08-21, before NASA Test 6 was run in `slabx` and before any
comparison against it.** Nothing above the `RESULTS` line is to be edited
afterwards.

This registration proposes **no code change**. It is a diagnosis, in the same
form as `PREREG_grid`: a hypothesis about an existing behaviour, tested by
re-running the model on inputs it already accepts. A submodel, if one is
warranted, is registered separately afterwards.

---

## The hypothesis

`PREREG_lh2_liftoff` established that ground reflection is not what keeps the
predicted concentration maximum on the ground: with the image term removed
entirely the ground-to-maximum ratio is 0.88 - 0.99 against a measured
0.10 - 0.20, because `z_c / sigma_z` reaches only 0.50 where about 1.8 - 2.1
is needed.

Backing the profile out of the FFI measurements (document 18 §18.10.5) gives,
across twelve arc-height sets:

| | median | range | spread |
|---|---|---|---|
| `sigma_z` model / required | **2.97** | 1.88 - 6.40 | 3.4x |
| `h` model / required | **1.90** | 1.19 - 4.10 | 3.5x |
| `z_c` model / required | 0.53 | 0.19 - 1.81 | 9.5x |

`sigma_z` and `h` exceed the required value at **twelve of twelve** points.
`z_c` does not, and scatters.

**The hypothesis is that the vertical extent of a positively buoyant cloud is
over-predicted by a factor of roughly two to three, and that this is general
rather than an artefact of the FFI array.**

The FFI result cannot settle it. Those sensors stop at 1.8 m while the model
puts the cloud depth at 10 - 12 m, so the diagnostic extrapolates the shape of
the bottom 15 %. An independent measurement of the vertical extent is needed,
and one exists.

## The target

**NASA White Sands Test 6.** As reported by Ichard, Hansen, Middha &
Willoughby (ICHS 2009, project file `115.pdf`), citing Witcofski &
Chirivella (1984) and Chirivella & Witcofski (1986):

| | |
|---|---|
| release | 5.11 m³ LH2 in 38 s = **9.5 kg/s** (rho_L 70.8 kg/m³) |
| pond | 9.1 m diameter, clay sides ~0.6 m, compacted sand |
| wind | **2.2 m/s at 10 m** |
| ambient | **15 °C**, RH **29 %** |
| roughness | **3 mm** |
| stability | **not reported in the original** |

Observed, and none of these is a concentration:

| | |
|---|---|
| **plume vertical extent** | **~20 m** |
| **detachment from the ground** | **~20 m downwind, 20.93 s after start** |
| plume downwind extent | 35 - 40 m |
| pool maximum radius | 2 - 3 m |
| complete evaporation | 43 s |

**Provenance warning.** These are values reported in a modelling paper that
read the originals. The NASA reports themselves have not been obtained. Until
NASA TM-83131 is read directly, every number here is second-hand, including
the statement that stability was not reported. This is the same situation as
Hall & Walker via Tickle (document 15 R3) and is recorded as such.

The release rate is **eleven times** the largest FFI trial and the wind is
**one third**, so this is not a repeat of the FFI conditions under another
name.

## Predictions

Cloud top is taken as `z_c + h/2` where the cloud is elevated and `h` where it
is grounded — the model's own `h_top`, which is what EQ 13 uses.

| # | Prediction | Criterion |
|---|---|---|
| **P-D1** | The vertical extent is over-predicted on NASA Test 6 as it is on FFI | model cloud top at the arc of maximum extent exceeds 20 m by a factor **between 1.5 and 4.0** |
| **P-D2** | The sign is specific to the buoyant case | on the ten LNG pool trials the cloud depth is **not** over-predicted by more than 1.5x relative to the depths implied by Hanna et al. (1993), who report dense-gas models under-predicting depth by about a factor of two |
| **P-D3** | The model does not detach where the measurement says it does | `z_c` stays **below `h/2`** throughout, so the cloud never leaves the ground, against an observed detachment at 20 m |
| **P-D4** | Stability governs detachment | sweeping B, D, F with everything else held, the arc at which `z_c / (h/2)` is largest moves **monotonically** toward the source as stability increases, and the ratio at F is at least **1.5 times** that at B |
| **NC1** | Nothing is changed | no coefficient, default or code path is modified; this is a re-run |

## What would falsify

**If P-D1 gives a factor below 1.5** the FFI diagnostic does not generalise
and the over-prediction is an artefact of extrapolating from the bottom 1.8 m.
The depth hypothesis is then withdrawn and document 18 §18.10.5 must be
downgraded to a statement about the FFI array only.

**If P-D1 gives a factor above 4.0** the effect is larger than the FFI
diagnostic implies and the two datasets disagree about its size, which is a
different problem and is to be reported as such rather than averaged.

**If P-D3 fails** — if the model does detach — then the deficiency is in where
and when, not whether, and the successor registration changes accordingly.

**P-D4 can fail independently of the others.** It tests the reading of
Ichard et al. that detachment appeared only under stable stratification. If
stability does not move detachment in `slabx`, that reading does not carry
over and document 20 §20.2 is wrong to connect it to §3.7.

## What must not happen

**No coefficient is to be adjusted in this test.** `a_entrain`, `c_mu_strat`
and the rest stay at Ermak's values. Document 18 §18.8 measured what fitting
costs: no coefficient produces the orientation difference at all, fitting the
bias to LH2 takes the LNG FAC2 from 0.90 to 0.20, and within LH2 alone the
between-trial spread grows from 4.71 to 5.50 as the bias is fitted out.

**`sigma_z` is not to be adjusted here or later on the strength of this
test.** NASA Test 6 is one trial. If it confirms the hypothesis it licenses a
*structural* proposal with its own registration and its own negative
controls — not a fitted depth.

**A failure of P-D1 is not to be rescued by choosing a different definition
of cloud top.** The definition is fixed above, before the run.

## Scope

One trial, and the quantity compared is a visual or inferred plume extent
rather than a profile measurement. **Grade C at best**, and the provenance is
second-hand. P-D3 and NC1 are deterministic.

Stability is unknown for this trial. P-D1 is evaluated at **D**, the neutral
default, and the B and F values are reported alongside so that the sensitivity
is visible rather than hidden in a choice.

---

## RESULTS

*(appended 2026-08-21 after the run; nothing above this line was edited)*

### The run

NASA Test 6 as specified above, source area taken as the pond
(9.1 m diameter, 65.0 m²), `EvaporatingPool`, CoolProp hydrogen.

| stability | cloud top max [m] | at x [m] | **top / 20** | max `z_c/(h/2)` | at x [m] | detaches? |
|---|---|---|---|---|---|---|
| B | 185.9 | 568 | **9.29** | 3.87 | 26.1 | yes |
| **D** | **563.5** | 604 | **28.17** | 64.8 | 140 | yes |
| F | 260.0 | 58 | **13.00** | 309.0 | 593 | yes |

### P-D1 — FAILED, and outside the falsifying band

The registered criterion was a factor between 1.5 and 4.0. At D the model
gives **28.17**. The registration states that a factor above 4.0 means the
effect is larger than the FFI diagnostic implies and that the two datasets
disagree about its size, to be reported rather than averaged. **That is the
outcome.**

### P-D3 — FAILED, and in the opposite direction to the prediction

The prediction was that `z_c` stays below `h/2` throughout, so that the cloud
never leaves the ground against an observed detachment at 20 m. **The model
detaches, and far too early and too far.** At D the cloud leaves the ground at
**x = 6.2 m** against an observed 20 m, and `z_c` then climbs without
turning over:

| x [m] | h [m] | z_c [m] | top [m] | sigma_z [m] | rho/rho_a | m_H2 |
|---|---|---|---|---|---|---|
| 0.81 | 2.47 | 0.00 | 2.47 | 1.43 | **0.789** | 0.212 |
| 4.78 | 3.87 | 0.35 | 3.87 | 2.03 | 0.812 | 0.181 |
| **6.16** | 4.02 | **2.51** | **4.52** | 1.16 | 0.830 | 0.159 |
| 13.22 | 3.78 | 24.72 | 26.61 | 1.09 | 0.884 | 0.107 |
| 35.71 | 4.61 | 103.7 | 106.0 | 1.33 | 0.952 | 0.053 |
| 116.6 | 8.46 | 273.6 | 277.8 | 2.44 | 0.992 | 0.014 |
| 540.8 | 21.2 | 534.0 | 544.6 | 6.11 | 1.000 | 0.001 |

### P-D4 — PARTIALLY FAILED

`F/B` = **79.9**, far above the registered 1.5. But the arc of maximum
`z_c/(h/2)` moves **away from** the source as stability increases
(x = 26 m at B, 140 m at D, 593 m at F), where the prediction required it to
move toward. **The direction is wrong.**

### P-D2 — NOT EVALUABLE

The LNG pool run gives cloud depths of 1.76, 2.36 and 4.34 m at 57, 140 and
400 m with `z_c` = 0 throughout. Hanna et al. (1993) report dense-gas models
under-predicting depth by about a factor of two, but that is a class statement
without per-trial depths, and no measured depth exists for these trials. The
prediction as registered cannot be scored. **Recorded as not evaluable rather
than as passed.**

### NC1 — PASSED

No coefficient, default or code path was modified. This was a re-run.

### Source-area sensitivity (post-hoc, reported not used)

The observed pool radius was 2 - 3 m; the pond radius is 4.55 m. The area is
an input choice and the choice was made before the run, so it does not rescue
P-D1, but it must be shown:

| pool radius [m] | area [m²] | top max [m] | top/20 | detachment x [m] | source rho/rho_a |
|---|---|---|---|---|---|
| 2.00 | 12.6 | 609 | 30.5 | 3.3 | 0.720 |
| 3.00 | 28.3 | 601 | 30.0 | 4.3 | 0.742 |
| 4.55 (used) | 65.0 | 563 | 28.2 | 6.2 | 0.789 |

**The conclusion does not turn on it.** Using the observed pool radius makes
the over-rise slightly worse and the detachment earlier.

### Status

| | |
|---|---|
| P-D1 | **FAIL** — 28.2 against a band of 1.5 - 4.0 |
| P-D2 | **not evaluable** |
| P-D3 | **FAIL** — the cloud detaches, at 6.2 m against an observed 20 m |
| P-D4 | **PARTIAL** — magnitude passes, direction fails |
| NC1 | **PASS** |
| hypothesis | **REJECTED as registered** |

### What this establishes, and it is not what the test was looking for

**The depth hypothesis is rejected and replaced by its opposite.** The FFI
diagnostic said the vertical extent is over-predicted by two to three and the
cloud will not leave the ground. On NASA Test 6 the cloud leaves the ground
almost immediately and rises to 560 m against an observed 20 m.

The two are not in conflict once the conditions are compared:

| | FFI Test 4 | NASA Test 6 |
|---|---|---|
| source | horizontal jet, 0.5 m | evaporating pool |
| release rate | 0.83 kg/s | **9.5 kg/s** |
| wind | 6.7 m/s | **2.2 m/s** |
| source `rho/rho_a` | 0.99 | **0.79** |
| `z_c` at 100 m | 1.8 m | **250 m** |

**The buoyant branch has no upper bound.** Where the buoyancy is weak and the
wind strong it produces a rise that happens to match the measurement; where
the buoyancy is strong and the wind weak it runs away. That is the signature
of a term that is present but unopposed, not of a term that is missing.

**This is the case `PREREG_added_mass` was about, now at field scale.** DRIFT's
authors reported that adding an added-mass term suppressed rise too much;
P-AM7 found that no coefficient of the oblate-spheroid form fits, because the
`B/h` shape function is wrong. NASA Test 6 shows what the absence costs: a
factor of 28 in a quantity that was directly observed.

**The FFI agreement at `z_c` was luck.** Document 18 §18.5 called it
surprising, §18.10.1 corrected that to "the branch working", and this run
corrects it again: the branch works there because the buoyancy is too weak for
the runaway to develop within 140 m. It is not evidence that the vertical
momentum balance is right.

### What the successor registration must address

Not the profile depth. **The vertical momentum balance has no mechanism that
limits rise**, and three candidates exist, none of them a fitted coefficient:

1. the added-mass term, whose shape function P-AM7 rejected — a different
   shape function is a structural proposal, not a re-run of that test
2. ambient stratification, which caps a rising plume at the mixing height or
   at a neutral-buoyancy level; the mixing height clamp is present
   (`z_c = min(z_c, h_mix - h/2)`) but `h_mix` is 1040 m at D and never binds
3. entrainment of ambient momentum into a rising cloud, which the shallow-layer
   form does not carry because it has one velocity

The detachment observation — **20 m downwind, 20.93 s** — is the target for
whichever is proposed, and it is a length and a time rather than a
concentration.

### Reproduction

```bash
cd lh2mod
python3 nasa6.py
```

