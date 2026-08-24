# slabx-lh2

Liquid hydrogen extensions to the [SLAB](https://github.com/lyullee/slabx)
dense-gas dispersion model, and a criterion that says **when the model may be
used at all**.

```bash
pip install slabx-lh2
```

---

## What this is for

A digital twin has to re-answer *how far does the flammable cloud reach* every
time the wind changes. CFD cannot do that inside a sensor update interval; an
integral model can, in about 100 ms.

But an integral model that answers outside its own premises is worse than no
answer, because the number looks the same either way. So this package does two
things: it fixes what LH2 breaks, and it tells you when to stop trusting the
result.

---

## The defect

`slabx.thermo.coolprop` clamps the temperature to the fluid's triple point
before every saturation query. That is a numerical guard, and for the released
substance it is harmless — hydrogen's triple point is 13.96 K.

**Water's is 273.16 K, and every cryogenic cloud is below it.**

```
  T [K]        stock        IAPWS   stock/IAPWS
 273.16   6.3424e+02   6.1166e+02           1.0
 260.00   6.3424e+02   1.9580e+02           3.2
 240.00   6.3424e+02   2.7267e+01          23.3
 200.00   6.3424e+02   1.6260e-01        3900.5
```

Water does not condense in a cryogenic cloud, so the latent heat that governs
LH2 buoyancy is never released. On the FFI pair that differs only in wind
speed, the uncorrected model gets the grounded/lofted contrast **backwards**.

This is not specific to slabx. Any dispersion code that reaches a real-fluid
property library for water and does not extend below the triple point has the
same behaviour.

## The criterion

SLAB's plume mode marches in `x`, which presumes the cloud is carried
downwind. Its own diagnostic is `w_c/u`:

```python
from slabx_lh2.diagnostics import applicability, critical_wind

critical_wind(9.5)             # 3.6 m/s at stability D: screen before running

status = applicability(traj)   # VALID | MARGINAL | OUT_OF_SCOPE
if status["fallback_required"]:
    raise RuntimeError(status["reason"])
```

Two quantities, and they are not the same. `critical_wind` answers from the
release rate and wind alone, **before** anything is integrated, and it is
fitted to a pool source, so it flags momentum jets conservatively.
`applicability` reads the trajectory the model actually produced, and it has
the authority.

Across 35 trials from four campaigns the screen and the diagnosis disagree
seven times — **every one in the conservative direction**, and every one a
jet. No case that the model refuses was let through by the screen.

**The worst case a separation distance is usually set from — a large release
in stable low wind — is outside the premise.** That is a property of
downwind-marching integral models, not of this implementation: Briggs's
bent-over plume formula rests on the same premise.

---

## Usage

```python
from slabx.core.plume import run_dispersion
from slabx.thermo.coolprop import CoolPropThermo, coolprop_water

from slabx_lh2.diagnostics import applicability
from slabx_lh2.lfl import flammable_distance
from slabx_lh2.plume_width import plume_width_coupling
from slabx_lh2.water_ice import with_sublimation

water = with_sublimation(coolprop_water())     # does not modify the argument

with plume_width_coupling():
    traj, used = run_dispersion(source, atm, emission, water, x_max=300.0)

if applicability(traj)["fallback_required"]:
    ...                                        # do not report the number

d = flammable_distance(traj, atm, t_avg=310.0, t_release=360.0)
print(d["raw"], d["factored"])                 # factored = raw x 1.25
```

`with_sublimation` returns a wrapper and is idempotent, so the same backend
can be used patched and unpatched in one process — which is what the negative
controls need.

`plume_width_coupling` is a context manager because the patch rebinds a
module-level name. **These patches are process-global and cannot be made
thread-safe** — the contended state is a global, not a resource. A second
thread wanting a different state raises `ConcurrentPatchError` rather than
silently getting the first thread's physics. **Run concurrent work in worker
processes**, and pre-warm them: a cold start is 3.4 s against 87 ms warm.

---

## What is in here

| module | what it is |
|---|---|
| `water_ice` | **a defect fix.** IAPWS sublimation below the triple point |
| `plume_width` | **a partial coupling.** Width follows the rise; off by default |
| `pool` | the pool radius is not free: evaporation balances delivery |
| `diagnostics` | `w_c/u`, `critical_wind`, `applicability`, Briggs `L_p`, `rise_scaling` |
| `lfl` | distance to 4 vol%, which is what a separation distance is set from |
| `air_condensation` | measured, and shown not to matter: onset is above the UFL |
| `vertical_drag` | **exploratory, not adopted.** Mack & Boot's form drag |
| `trials` | conditions for 35 trials; the measurements are not distributed |

**No new coefficients.** Every constant is a physical constant, a published
reference value, or a number already in SLAB's coefficient table.

---

## Verification

**Negative controls first.** Every module was adopted on the condition that it
leaves the limits the original SLAB validation rests on alone.

> **The defect is not specific to hydrogen.** Run the same LNG trial with the
> CoolProp water backend and the correction moves the LFL distance by
> **13.8 %**: Burro 8's cloud runs from 208 to 290 K and 25 of its 58
> trajectory points are below the water triple point. Any cryogenic release
> into humid air that reaches a real-fluid library for water is affected.
> **This correction was adopted upstream in slabx 1.0.6.**

| | |
|---|---|
| the published dense-gas validation | **cannot be reached** — it runs on the legacy water backend, which was never clamped |
| Prairie Grass, passive | **bit-identical** |
| the width coupling on any cloud that does not loft | **bit-identical** |

**A 2x2 ablation separates the two corrections completely.** On the FFI trials
the width coupling changes nothing — it is gated on lofting and none of them
lofts — and the bracket result is produced by the water correction alone. On
the NASA trials the reverse holds. Neither does anything in the other's
regime, so the causal claims stand separately.

**The quantity that matters.** Sensor concentrations swing with an assumed
humidity that FFI never reported: the model's FAC2 runs from 0.42 to 0.92
across a plausible range. **The LFL distance does not move**, because it is
set by where a profile crosses a threshold rather than by its level.

Against the FFI outdoor trials, whose three arcs bracket the measured
distance: **five of six fall in the bracket, and the failure is on the
non-conservative side.** The minimum factor those six require is **1.114**;
`SAFETY_FACTOR` is **1.25**, examined as a rounded engineering margin.

> **It is derived and evaluated on the same six trials and is not an
> independently validated safety factor.** No other dataset brackets an LFL
> distance. Say "sufficient for the six trials considered".

## When not to use this

| scenario | |
|---|---|
| pipe or hose jet, u > 3 m/s | usable |
| tanker transfer, u > 5 m/s | usable |
| **bunkering spill, u < 4 m/s** | **outside the premise** |
| **small release, stable and calm, u < 2.5 m/s** | **outside the premise** |

Three things are known to be wrong and are not fixed:

- **A horizontal high-momentum jet's peak concentration is under-predicted by
  about 2.6x.** EFFECTS and Phast/UDM report the same; it appears in the LFL
  distance only as the factor of 1.11 above.
- **Large buoyant releases still rise too far, and the shortfall is
  located.** Writing `dz/dx = Gw/(Ru)` with `R ~ z^s` gives an exponent of
  `2/(s+1)` where `s = dlnB/dlnz + dlnh/dlnz`. Briggs needs `s = 2`; the model
  reaches 0.6 to 1.0, because **the depth is not coupled to the rise at all**.
  The prediction matches the fitted exponent to 6 % on all four NASA trials,
  so this is a located missing term rather than an unexplained residual.
- **Ground conduction does not transfer between substrates.** The cryogenic
  diffusivity of concrete differs by three to five times between two
  campaigns. Take the pool regression rate from measurement rather than
  computing it.

---

## Data

**This package ships trial conditions, not trial measurements.**

The conditions are the experiments' settings and nobody can run the model
without them. The measurements are the reports' findings, and redistributing
those is the originating organisation's decision.

Nothing is withheld that cannot be obtained: **[`data/SOURCES.md`](data/SOURCES.md)**
names the report behind each set and `scripts/extract/` turns those reports
back into exactly the CSVs this work used.

Without them, everything that is a model output or an internal comparison
still runs — the defect, the negative controls, the applicability diagnostic,
the runtime benchmark, the ablation, the map. Those are the grade-A results
and they carry the two main claims. The comparisons against measurement skip,
visibly, rather than being deleted.

```bash
export SLABX_LH2_DATA=/path/to/extracted/csvs
pytest                                  # the skipped comparisons now run
```

---

## Reproduce

```bash
pip install -e ".[test,figures]"
pytest                                  # comparisons against measurement skip
python scripts/reproduce.py --json      # every headline number
python scripts/build_dataset.py         # data/catalogue.{json,csv}
python scripts/figure_applicability.py  # the applicability map
python scripts/benchmark_runtime.py     # runtime, on your hardware
python scripts/ablation_2x2.py          # which correction did what
python scripts/applicability_all.py     # screen against diagnosis, all cases
```

**Numbers that go into a paper should come from `results/results.json`, not be
typed from a document.** `data/catalogue.csv` maps each quantity to its grade,
its provenance, and whether it has been withdrawn — seven values in this
project were, and they are kept there so that anyone who finds one in an old
draft can look it up.

## Method

Every hypothesis was registered before it was tested, with its negative
controls and its falsification conditions. **Nine registrations, six
rejected** — ground reflection, cloud depth, pre-lift-off vertical drag,
rise-dependent entrainment, added mass, an impinging-jet source.

The rejections are the more useful half. `PREREG_lh2_rise_entrainment` proved
algebraically that SLAB's buoyancy source term is a conserved flux that no
entrainment change can reduce, which rules out an entire family of attempts.

One rule, arrived at the hard way:

> **Do not decide on absolute concentrations.** Decide on deterministic
> internal comparisons, on reference correlations, or on directly measured
> lengths, times and binary events.

FFI Tests 3 and 5 differ by 2 % in rate and 10 % in wind; their measured
maxima differ by ±22 % and the height of the maximum flips. Four of the six
rejected registrations chased effects smaller than that.

## Licence

MIT for the code. The experimental data is not redistributed; see
[`data/SOURCES.md`](data/SOURCES.md).

## Citation

See `CITATION.cff`. Please cite the SLAB model as well:

> Ermak, D.L. (1990). *User's Manual for SLAB: an atmospheric dispersion model
> for denser-than-air releases.* UCRL-MA-105607, Lawrence Livermore National
> Laboratory.
