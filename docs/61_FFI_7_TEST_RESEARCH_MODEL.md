# Seven-test FFI research model

Status: frozen research configuration, 2026-10-01.  This record describes the
model used for the planned paper.  It is not a production qualification or a
claim of whole-field conformance.

Archived software release: **slabx-lh2 0.2.0**,
[10.5281/zenodo.23084445](https://doi.org/10.5281/zenodo.23084445).
Generic core release: **slabx 1.0.8**,
[10.5281/zenodo.23084448](https://doi.org/10.5281/zenodo.23084448).

## Model architecture

The calculation is a chain of explicit physical responsibilities:

1. an LH2 source route resolves flashing, phase state, jet or impact behaviour,
   and any pool contribution;
2. where the resolved-source route is used, a source ledger records rate,
   composition, temperature, density, geometry, direction and physical stage
   at a selected handoff plane;
3. `PhysicalTransitionCloud` converts a pre-diluted resolved state into the
   generic SLABx `SourceModel` contract;
4. SLABx integrates mass, species, momentum and energy in plume mode and, for
   a finite release, changes to puff mode from the emitted H2 inventory;
5. the observation operator samples the predicted field at the reported
   sensor radius, bearing and height;
6. diagnostics report continuous concentration error and threshold decisions
   separately.

The SLABx plume/puff equations and atmospheric transport are material
independent. Flashing, cryogenic H2 properties, condensation or freezing of
air components, release orientation, impact/pool routing and H2 flammability
thresholds are LH2-specific.

## Corrected finite-release clock

At a downstream handoff plane the cloud contains emitted H2 and already
entrained air. The state flux is therefore a mixture flux, but the SLABx
species accumulator is an H2 inventory. `PhysicalTransitionCloud.total_mass`
and `released_mass(t)` use H2 mass so that the plume-to-puff decision compares
like with like. `carrier_total_mass` and `carrier_released_mass(t)` expose the
H2+air inventory separately.

Using carrier mass as `total_mass` compares H2 accumulated in the cloud with
H2+air released at the source. In the five-second FFI packets this can delay or
prevent the physical finite-release transition.

## Frozen evaluation

The frozen evaluation covers FFI Tests 1--7 and 210 sensor-test records. No
sensor concentration fitting, residual correction, or sensor-hull assimilation
is active.

| Metric | Frozen value |
|---|---:|
| MAE | 0.086463 vol% |
| bias | -0.014593 vol% |
| RMSE | 0.132241 vol% |
| nominal 0.5LEL classification (2 vol%) | 209/210 |
| reporting-precision-compatible 0.5LEL classification | 210/210 |
| LFL classification (4 vol%) | 210/210 |

| FFI test | MAE (vol%) | bias (vol%) | RMSE (vol%) | 0.5LEL | LFL |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.052372 | -0.038204 | 0.066816 | 30/30 | 30/30 |
| 2 | 0.048993 | -0.002248 | 0.089180 | 30/30 | 30/30 |
| 3 | 0.099159 | -0.031246 | 0.144161 | 30/30 | 30/30 |
| 4 | 0.106088 | -0.065971 | 0.171129 | 29/30 | 30/30 |
| 5 | 0.099852 | 0.018397 | 0.128772 | 30/30 | 30/30 |
| 6 | 0.102383 | 0.028412 | 0.148089 | 30/30 | 30/30 |
| 7 | 0.096390 | -0.011290 | 0.146344 | 30/30 | 30/30 |

The one nominal 0.5LEL disagreement is a Test 4 boundary case: the reported
value is 2.0 vol% and the prediction is approximately 1.98 vol%. It agrees
when the report's 0.1 vol% display precision is applied. This precision check
is reported separately and is not used to replace the nominal result.

## Physical result from the model

With the corrected species clock, applying the native finite-source relation
to each *isolated* five-second Test 4 cohort gives a plume-to-puff transition
distance of 30.8148--32.9902 m over 72 reconstructed paths (median
31.8257 m). In this diagnostic, individual-cohort states at 30 m precede the
calculated transition and states at 50 and 100 m follow it. Native puff
dynamics give a post-transition scalar concentration with a median puff/plume
ratio of 0.842 and a range of 0.611--0.995 in the audited isolated cases.
The range depends on the chosen cohort duration: the 30/50 m ordering persists
for 5--10 s cohorts but not for every tested duration.

The 360 s release contains overlapping cohorts. This diagnostic does not
establish an observed transition boundary, or validate a coupled puff solution,
for that complete cloud. A live vector-weather puff implementation remains a
follow-up task; a dose-preserving arrival-duration remap alone did not improve
the error.

## Interpretation and limits

Threshold classification and pointwise concentration error answer different
questions. Test 4 and Test 6 retain geometry-organised continuous-field
residuals even though LFL classification is 210/210. The research result
supports rapid safety-region screening within the tested configuration, while
the remaining residual structure prevents a production-default claim.

Six tests used ten bearings on 30, 50 and 100 m arcs. Test 2 is different:
it used eight bearing positions on the 30 m arc and two near-source positions
at 9.010 and 11.043 m, each measured at three heights. The seven tests still
provide 30 records each, but Test 2 must not be described as a three-arc
layout. Test 2 used a separate meteorology-conditioned direction envelope;
its field route did not use the resolved-source `SourceLedger` handoff.

The saved Test 6 screen covered 677 eligible artifact folders, but these
contained only 29 distinct complete 30-receptor prediction vectors. All 476
folders satisfying the aggregate-error and threshold gates reproduced the
retained vector exactly. They are repeated outputs, not 476 independent model
improvements or failed independent coefficient trials. No distinct saved
alternative passed the joint gate.

Time-resolved wind direction can establish whether a receptor direction has
support. It does not, by itself, determine concentration, residence time or
dilution. Directional support and concentration conditional on that support
must therefore remain separate operators.

## Reproducibility record

The private research workspace completed 182 regression tests. Its frozen
audit contains 36 successful declared cases with 182 declared artifacts; after
separating one live workspace inventory, 35 deterministic cases and 175 files
were byte-stable, with the seven-file live inventory complete. These audit
artifacts include third-party-derived sensor data and are not redistributed in
this public package.

The public repository provides the reusable source contract, unit tests,
source provenance, and extraction instructions. Rebuilding the measurement
comparison requires the FFI report obtained from its publisher and the private
research workflow that produced the frozen audit.

The archived software DOI above identifies the public 0.2.0 code release,
not a frozen archive of the private 210-record research workflow. A paper
reproducibility deposit still needs the permissible derived data, exact inputs,
scripts, manifests and output hashes.

## Relationship to the earlier six-test result

The six-test LFL-bracket study in this repository is retained as a historical,
separately scoped validation. Its humidity assumptions and endpoint metrics
must not be combined with the seven-test, 210-record concentration evaluation
above. The planned paper uses the seven-test frozen result.
