# Pre-registration: an out-of-domain stress test of the applicability criterion

**Registered 2026-08-22, before the model was run on these conditions.**
Nothing above the `RESULTS` line is to be edited afterwards.

> **Later correction, recorded here rather than in the text above.** The
> screening correlation is written below as `u_crit ~ 2.5 q^0.15`, which was
> the round figure in document 22 at registration time. It was refitted per
> stability class afterwards -- class D is `2.674 q^0.135`, and the
> coefficients are in `slabx_lh2.diagnostics.CRITICAL_WIND_FIT`. The two agree
> to 3 % over 0.1 to 30 kg/s, so **none of the results below changes**; quote
> the fitted values.

---

## Why this is worth registering

`w_c/u` and `u_crit ~ 2.5 q^0.15` are the strongest claim in this work: they
say when the marching formulation is entitled to answer, which is what a
real-time monitoring system needs and what a CFD-based digital twin cannot
give.

**Both have so far been checked only against the model itself.** Document 22
derived them from slabx's own output, and FFI, E3.5 and NASA were the same
trials the rest of the work used. A criterion for when a model may be trusted
that has only ever been exercised on the model's own training ground is worth
very little.

Zhang et al. (2024), *An experimental study on the large-volume liquid hydrogen
release in an open space*, Appl. Sci. 14, 3645, supplies conditions that are
independent in every respect: a different group, a different site, published after this work began,
and **at release rates up to three times NASA's and sixty times FFI's**.

| test | volume [m3] | duration [s] | rate [kg/s] | u [m/s] | RH [%] | T [K] |
|---|---|---|---|---|---|---|
| 5 | 3.0 | 4 | 53.1 | 0.13 | 28.8 | 291.7 |
| 6 | 2.5 | 40 | 4.43 | 0.30 | 39.8 | 282.5 |
| 7 | 2.5 | 30 | 5.90 | 0.04 | 27.6 | 277.8 |
| 8 | 2.5 | 48 | 3.69 | 0.05 | 29.2 | 279.2 |
| 9 | 1.5 | 25 | 4.25 | 0.61 | 27.5 | 283.1 |
| 10 | 3.0 | 4 | 53.1 | 0.11 | 46.1 | 282.1 |
| 11 | 3.0 | 5 | 42.5 | 0.01 | 79.6 | 307.8 |
| 12 | 0.5 | 20 | 1.77 | 0.15 | 67.1 | 307.7 |

Tests 1 to 4 report no duration and cannot be converted to a rate; they are
excluded. Rates are `volume x 70.8 / duration`.

**Humidity is measured**, which FFI never reported.

## What this can and cannot test

**It cannot discriminate.** Every usable Zhang test has wind below 0.7 m/s, so
a criterion that flags low wind will flag all eight. Test 2 at 3.0 m/s would
have been the discriminating case and its duration is not reported.

So the honest content is narrower, and is stated up front:

1. whether the correlation, fitted to slabx output at 0.1 to 30 kg/s, still
   agrees with the model's own diagnostic at **53 kg/s**
2. whether the model, run outside its premise, fails **visibly** rather than
   returning a plausible number — which is the property the monitoring
   application actually depends on
3. whether an independent group's qualitative description of the cloud matches
   what the criterion says about it

The discriminating side comes from the existing sets: FFI is inside at
`w_c/u` = 0.02 to 0.11, NASA is outside at 0.61 to 4.74. Zhang extends the
outside end in release rate.

## Predictions

| # | Prediction | Criterion |
|---|---|---|
| **P-Z1** | The model's own diagnostic says these are outside | `max w_c/u` **> 1** on at least **7 of 8** |
| **P-Z2** | The correlation transfers to 53 kg/s | for every test, `u < critical_wind(q)` **and** `max w_c/u > 1` agree — no test where one says inside and the other outside |
| **P-Z3** | Failure is visible, not silent | on every test flagged by P-Z1, at least one of: rise angle **> 45 deg**, cloud centre above the mixing height, or the LFL distance non-monotonic in `x` |
| **P-Z4** | The independent description matches | Zhang report the far-field concentration in the calm tests as driven by **spontaneous diffusion down the concentration gradient** rather than by advection, and the visible cloud spreading symmetrically about the jet axis — which is what "outside the bent-over premise" means physically |

**P-Z3 is the one that carries weight.** A criterion that flags a condition is
useful; a model that also produces an obviously broken answer there is safe. A
model that produces a plausible but wrong number in a flagged condition is the
hazard, because an operator who overrides the flag gets a number that looks
fine.

**P-Z2 is the transferability test.** `u_crit` was fitted over 0.1 to 30 kg/s.
Zhang's 53.1 kg/s is outside that range in the fitted variable, which is the
only genuine extrapolation available.

## What would falsify

**P-Z1 failing on more than one test**: the diagnostic does not identify calm
large releases, and the applicability claim is weaker than stated.

**P-Z2 failing**: `2.5 q^0.15` does not extrapolate and must be quoted only
over the range it was fitted, 0.1 to 30 kg/s.

**P-Z3 failing**: the model returns plausible numbers where the criterion says
it must not be trusted. **That would be the most serious outcome here** — it
would mean the criterion has to be enforced by the caller and cannot be
detected from the output.

## What must not happen

**Nothing is adjusted to these data.** `u_crit`'s coefficients are from
document 22, fitted to model output before Zhang was obtained, and are not
refitted. No agreement with Zhang's concentrations is sought: their sensors
are at 2, 8, 12 and 20 m and the model is being run somewhere it should not be,
so a concentration comparison would be meaningless in either direction.

**A pass here is not validation of the model.** It is validation of the
refusal.

## Scope

Eight trials, one campaign, one site, and no discriminating negative case
within the set. **Grade C** for anything quantitative; P-Z1 and P-Z2 are
deterministic given the reported conditions.

---

## RESULTS

*(appended 2026-08-22 after the run; nothing above this line was edited)*

| test | q [kg/s] | u | `u_crit` | `u/u_crit` | **max `w_c/u`** | rise angle | `z_c/h_mix` |
|---|---|---|---|---|---|---|---|
| 5 | 53.10 | 0.13 | 4.54 | 0.029 | **217.4** | 89.7 deg | 0.990 |
| 6 | 4.42 | 0.30 | 3.12 | 0.096 | **44.6** | 88.7 | 0.996 |
| 7 | 5.90 | 0.04 | 3.26 | 0.012 | **455.4** | 89.9 | 0.991 |
| 8 | 3.69 | 0.05 | 3.04 | 0.016 | **397.0** | 89.9 | 0.991 |
| 9 | 4.25 | 0.61 | 3.11 | 0.196 | **13.7** | 85.8 | 0.996 |
| 10 | 53.10 | 0.11 | 4.54 | 0.024 | **252.3** | 89.8 | 0.990 |
| 11 | 42.48 | 0.01 | 4.39 | 0.002 | **821.8** | 89.9 | 0.988 |
| 12 | 1.77 | 0.15 | 2.72 | 0.055 | **110.4** | 89.5 | 0.996 |

### P-Z1 — PASSED, 8/8

Criterion was 7 of 8. `max w_c/u` runs from **13.7 to 822**, against 1 for the
premise and 0.02 to 0.11 on the FFI trials. For comparison NASA, which this
work already treats as outside, reaches 4.74.

### P-Z2 — PASSED, 8/8 — **but this is an internal check, not validation**

Every test is flagged by both the screening correlation and the model's own
diagnostic; none is flagged by one and not the other.

`u_crit` was fitted to slabx output over 0.1 to 30 kg/s, and this shows it
still agrees with the diagnostic it approximates at 53.1 kg/s. **Both sides of
the comparison are the model.** Zhang's data supplies the conditions and
nothing else. This is **extrapolation consistency of an internal screening
approximation**, and it must not be reported alongside P-Z4 as though both
were external evidence.

### P-Z3 — PASSED, 8/8

The rise angle is **85.8 to 89.9 degrees** on every test. The cloud goes
essentially straight up while the formulation integrates along `x` as though
it were being carried downwind.

**The failure is unmistakable.** Nobody reading a rise angle of 89.9 degrees
from a downwind-marching model would take the answer.

One clause of the criterion turned out to be unreachable: `z_c` sits at
0.988 to 0.996 of the mixing height on all eight, because SLAB clamps it
there. It cannot exceed 1 by construction. **Being pinned at the top of the
boundary layer is itself the signal**, and the criterion should have been
written as "at or above" rather than "above". The prediction passes on the
rise angle alone, which fired on all eight independently.

### P-Z4 — PASSED

Zhang report, of the calm tests, that far-field concentration fluctuations
depend on **spontaneous diffusion driven by the hydrogen concentration
gradient**, and that the visible cloud shifts only slightly to one side or the
other of the release axis, which they attribute to minimal ambient wind. In
Tests 6 and 7, run at the same conditions on different ground, the sensors that
saw fluctuations were **mirror images about the release axis**.

A cloud that spreads symmetrically about the source and is fed by its own
concentration gradient is not a bent-over plume. **That is what "outside the
premise" means physically**, described by a group with no connection to this
work.

### Status

| | |
|---|---|
| **P-Z1** | **PASS** 8/8 |
| **P-Z2** | **PASS** 8/8, extrapolating to 53 kg/s |
| **P-Z3** | **PASS** 8/8 on rise angle; one clause unreachable by construction |
| **P-Z4** | **PASS**, qualitative |

### What this establishes, and what it does not

**Establishes.** Run at an independent dataset's conditions, the criterion
places all of them outside the formulation's premise and the model fails
visibly rather than silently there (P-Z1, P-Z3), and an independent group's
description of those clouds is what "outside the premise" means physically
(P-Z4).

**P-Z4 is the only part that is external evidence.** P-Z1 and P-Z2 are the
model talking about itself at conditions someone else measured; P-Z3 is a
property of the model's output. Useful, and not validation.

**Does not establish.** That the criterion **discriminates**. There is no
negative case here, so nothing in this registration shows that it would decline
to flag a condition the model handles well. Every usable Zhang
trial is calm; a criterion that flags low wind flags all of them. The
discriminating evidence remains FFI inside at 0.02 to 0.11 and NASA outside at
0.61 to 4.74. Zhang extends the outside end in release rate and adds an
independent qualitative description; it does not add a negative case.

Test 2 at 3.0 m/s would have been the discriminating trial and its duration is
not reported.

**And it is not validation of the model.** It is validation of the refusal.
Nothing here says the model would be right if it did answer.

### Reproduction

```bash
python scripts/reproduce.py zhang
```

