# slabx-lh2

Liquid hydrogen extensions to the [SLAB](https://github.com/lyullee/slabx)
dense-gas dispersion model, and a criterion that says **when the model may be
used at all**.

```bash
pip install slabx-lh2
```

For an evidence-qualified LH2 pool source term, install the optional adapter:

```bash
pip install "lh2poolx @ git+https://github.com/lyullee/lh2poolx.git"
```

---

## What this is for

A digital twin has to re-answer *how far does the flammable cloud reach* every
time the wind changes. Re-running high-fidelity CFD across a scenario bank is
generally impractical inside a sensor update interval; this integral model
is intended for rapid scenario screening. The included benchmark records
single-case latency and complete-bank throughput on the user's own hardware;
runtime figures are host- and load-specific and are not a comparison with
other codes.

But an integral model that answers outside its own premises is worse than no
answer, because the number looks the same either way. So this package does two
things: it fixes what LH2 breaks, and it tells you when to stop trusting the
result.

---

## The historical water-property defect

Through slabx 1.0.4, `slabx.thermo.coolprop` clamped water saturation at the
triple point. Version 1.0.5 corrected the pressure and 1.0.6 added the fusion
enthalpy. This package detects those behaviours independently, supplies only
what is missing, and does nothing when both are already present.

**Water's triple point is 273.16 K, and near-field cryogenic mixtures can pass
well below it.**

```
  T [K]   reconstructed clamp        IAPWS   clamp/IAPWS
 273.16   6.3424e+02   6.1166e+02           1.0
 260.00   6.3424e+02   1.9580e+02           3.2
 240.00   6.3424e+02   2.7267e+01          23.3
 200.00   6.3424e+02   1.6260e-01        3900.5
```

The old clamp suppresses deposition/condensation below the triple point and
omits the fusion contribution to latent heat. On the FFI pair that differs
only in wind speed, the reconstructed pre-correction model gets the
grounded/lofted contrast **backwards**.

The failure mode is not conceptually specific to slabx: any implementation
that evaluates water properties below the triple point must define a valid
solid--vapour treatment rather than silently clamp or extrapolate a
liquid--vapour relation.

## The routing diagnostic

SLAB's plume mode marches in `x`, which presumes the cloud is carried
downwind. Its own diagnostic is `w_c/u`:

```python
from slabx_lh2.diagnostics import premise_summary, critical_wind

critical_wind(9.5)             # optional reference-pool warning, not a decision

status = premise_summary(traj)
if status["violated"]:
    raise RuntimeError("outside the bent-over premise; do not use this number")
```

Two quantities, and they are not the same. `critical_wind` is an inherited,
input-only emulator fitted to one stated pool reference geometry. It is useful
only as an optional warning and must not accept or withhold an endpoint.
`premise_summary` reads the completed trajectory and supplies the routing
signal. The manuscript uses only the post-run `max(w_c/u) > 1` condition and
reports the continuous ratio; it does not use the fitted warning as scientific
evidence.

**The worst case a separation distance is usually set from — a large release
in stable low wind — is outside the premise.** That is a property of
downwind-marching integral models, not of this implementation: Briggs's
bent-over plume formula rests on the same premise.

---

## Usage

```python
from slabx.core.plume import run_dispersion
from slabx.thermo.coolprop import CoolPropThermo, coolprop_water

from slabx_lh2.diagnostics import premise_summary
from slabx_lh2.lfl import flammable_distance
from slabx_lh2.plume_width import plume_width_coupling
from slabx_lh2.water_ice import with_sublimation

water = with_sublimation(coolprop_water())     # does not modify the argument

with plume_width_coupling():
    traj, used = run_dispersion(source, atm, emission, water, x_max=300.0)

if premise_summary(traj)["violated"]:
    ...                                        # do not report the number

d = flammable_distance(
    traj, atm, t_avg=310.0, t_release=360.0, safety_factor=1.0
)
print(d["raw"])                                # raw operational endpoint
```

`with_sublimation` returns a wrapper and is idempotent. The deliberate
historical clamp is reserved for ablation tests, not operational prediction.

`plume_width_coupling` is a context manager because the patch rebinds a
module-level name. **These patches are process-global and cannot be made
thread-safe** — the contended state is a global, not a resource. A second
thread wanting a different state raises `ConcurrentPatchError` rather than
silently getting the first thread's physics. **Run concurrent work in worker
processes**, and pre-warm them: the measured cold-start median is 1.49 s
against 67 ms warm, about 22 times slower.

---

## What is in here

| module | what it is |
|---|---|
| `water_ice` | **compatibility correction.** Pressure and fusion checks; no-op on slabx 1.0.6 |
| `plume_width` | **a partial coupling.** Width follows the rise; off by default |
| `pool` | the pool radius is not free: evaporation balances delivery |
| `lh2pool` | optional adapter from `lh2poolx` to a SLAB `EvaporatingPool` |
| `diagnostics` | `w_c/u`, `critical_wind`, `applicability`, Briggs `L_p`, `rise_scaling` |
| `lfl` | distance to 4 vol%, which is what a separation distance is set from |
| `air_condensation` | measured, and shown not to matter: onset is above the UFL |
| `vertical_drag` | **exploratory, not adopted.** Mack & Boot's form drag |
| `trials` | conditions for 35 trials; the measurements are not distributed |

No coefficient was fitted to the six FFI LFL distances. The legacy
`critical_wind` warning does contain coefficients fitted to the frozen model's
own `max(w_c/u) = 1` boundary for one reference pool; this is why it is not used
as a physical correlation or an authoritative gate.

`lh2poolx` is deliberately upstream of SLAB. It supplies a declared
quasi-steady, unconfined pool area and evaporation rate from flash, an explicit
ground-deposition fraction and a ground heat-transfer assumption. It does not
infer jet impact, splash, drainage or a confined-pool inventory. The adapter
refuses a source with unresolved accumulation rather than silently passing it
to the dispersion calculation.

---

## Verification

**Negative controls first.** Every module was adopted on the condition that it
leaves the limits the original SLAB validation rests on alone.

> **The mechanism is not hydrogen-specific.** A deliberate
> clamped-versus-corrected CoolProp-water ablation moves Burro 8's LFL distance
> by **13.54 %**. This is cross-fluid evidence about sub-triple-point water
> treatment, not a claim that slabx 1.0.6 remains defective.

| | |
|---|---|
| hydrogen-only width gate on ten LNG trials | **bit-identical (0.0 %)** |
| Prairie Grass, passive | **bit-identical** |
| the width coupling on any cloud that does not loft | **bit-identical** |

**A 2x2 ablation separates the two corrections completely.** On the FFI trials
the width coupling changes nothing — it is gated on lofting and none of them
lofts — and the bracket result is produced by the water correction alone. On
the NASA trials the reverse holds. Neither does anything in the other's
regime, so the causal claims stand separately.

The accessible FFI report does not tabulate relative humidity. Across RH
0--100 %, both horizontal trials remain under-predicted. Direct bisection gives
bracket-count transitions at RH 56.3 % and 59.5 %: three of six below 56.3 %,
four from 56.3 % to 59.5 %, and five at and above 59.5 %. The table below is
therefore explicitly an illustrative RH 75 % calculation.

At the illustrative RH = 75 % calculation, five of six raw endpoints lie in
the observation-defined brackets and Test 4 misses on the non-conservative
side. The ratio 50/44.891 = **1.113809** describes that same-set discrepancy;
it is not rounded, applied, or recommended as a transferable safety factor.
The legacy `SAFETY_FACTOR = 1.25` symbol remains in version 0.1.3 for API and
DOI reproducibility only. New analyses should pass `safety_factor=1.0` and use
the raw result. No other dataset here independently brackets an LFL distance.

## When not to use this

| condition | action |
|---|---|
| obstacle, enclosure, dike interaction, impingement, or recirculation controls the result | route to a separately qualified geometry-resolving or emergency layer |
| post-run `max(w_c/u) > 1` | withhold the endpoint and route; rise exceeds downwind advection |
| post-run `max(w_c/u) <= 1` | report the raw endpoint together with the continuous ratio and all source/geometry caveats; this is not universal validation |
| reference-pool `critical_wind` warning only | prepare an alternative route, but do not withhold or accept an endpoint from this warning alone |

The legacy `applicability()` function also returns `VALID` and `MARGINAL`
display labels separated at 0.5. That lower band has no independent physical or
experimental basis and is not used as a scientific decision in the manuscript.

Three things are known to be wrong and are not fixed:

- **Horizontal high-momentum near-field maxima are under-predicted.** Across
  RH = 0--100 %, the 30 m model/measurement ratios remain about 0.38--0.39 for
  Test 4 and 0.29--0.40 for Test 6. No distance factor is inferred from this.
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
python scripts/fit_critical_wind.py     # refit the pre-run screening curves
python scripts/benchmark_runtime.py     # runtime, on your hardware
python scripts/ablation_2x2.py          # which correction did what
python scripts/applicability_all.py     # screen against diagnosis, all cases
```

For the manuscript's i9-12900K reference run on Windows, use the strict
one-command runner below. It refuses a different CPU, preserves any existing
output, verifies the required row counts and failures, and writes a separate
`validation.txt`. A p99/p50 ratio above 1.30 is retained and marked `WARN`
rather than discarded.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_i9_benchmark.ps1
```

**Generated numbers should come from machine-readable outputs, not be typed
from a document.** `results/results.json` contains model-only results in the
measurement-free installation; measurement-dependent comparisons are present
only after the source reports have been obtained as described in
`data/SOURCES.md`. `data/catalogue.csv` maps each distributed quantity to its
grade, provenance, and withdrawal status.

## Method

Each evaluated modification was registered before it was tested, with its
negative controls and falsification conditions. Rejected paths include ground
reflection, cloud depth, pre-lift-off vertical drag, rise-dependent
entrainment, added mass, and an impinging-jet source.

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
