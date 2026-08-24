"""
Every number this project produced, in one file.

    python scripts/build_dataset.py

Writes `data/catalogue.json` and `data/catalogue.csv`: one record per
quantity, with its value, where it came from, what grade it carries, and
whether it has been retracted.

Why this exists
---------------
The numbers live in three places and only one of them is regenerated:

    data/*.csv          transcribed measurements, stable
    results/results.json  computed on demand from those, always current
    docs/*.md           written by hand, and **109 figures appear only there**

The third is where a retracted value survives. Thirteen have been corrected in
this project and five had to be hunted down afterwards. So everything that
only existed in prose is written down here with its provenance, including the
values that were withdrawn -- a retraction is only useful if the retracted
value is recorded next to it.

Fields
------
    key         dotted path, unique
    value       the number, or a short string for a verdict
    unit
    grade       A | B | C | -   (docs/07 scheme; see `GRADES` below)
    kind        measurement | model | comparison | diagnostic | withdrawn
    source      where it came from
    doc         the document that discusses it
    note        anything a reader needs before quoting it

**A record with `kind = "withdrawn"` must never be quoted as a result.** It is
here so that someone who finds the number in an old draft can look it up and
see that it was retracted, and why.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

GRADES = {
    "A": "deterministic: a model-internal comparison, or a reference "
         "correlation. Re-running gives the same number.",
    "B": "compared against measurement, where the measured quantity is a "
         "length, a time, or a binary event.",
    "C": "compared against measurement, where the target is a concentration, "
         "or the trials are few, or an unmeasured input is assumed.",
    "-": "not a claim: a condition, an input, or a piece of provenance.",
}

#: key, value, unit, grade, kind, source, doc, note
RECORDS: list[tuple] = [

    # ---------------------------------------------------------------- water
    ("water.clamp.error_at_260K", 3.2, "-", "A", "comparison",
     "CoolPropThermo vs IAPWS sublimation", "23, 26",
     "the stock backend returns the triple-point value at every T below it"),
    ("water.clamp.error_at_240K", 23.3, "-", "A", "comparison",
     "CoolPropThermo vs IAPWS", "23, 26", ""),
    ("water.clamp.error_at_200K", 3900.0, "-", "A", "comparison",
     "CoolPropThermo (slabx <= 1.0.5) vs IAPWS", "23, 26, 42",
     "the headline figure. **slabx 1.0.6 fixed this upstream**, and against "
     "1.0.6 the ratio is 1; the number records what the defect was, not what "
     "the current release does"),
    ("water.clamp.error_at_150K", 1.0e8, "-", "A", "comparison",
     "CoolPropThermo vs IAPWS", "23, 26", ""),
    ("water.iapws.accuracy_to_230K", 0.03, "fraction", "A", "comparison",
     "Wagner, Riethmann, Feistel & Harvey 2011", "23",
     "the sublimation curve against the Magnus reference"),
    ("water.fusion_enthalpy", 333400.0, "J/kg", "-", "measurement",
     "IAPWS", "23", "added below the triple point; a physical constant"),

    # ------------------------------------------------------- negative control
    ("negctl.lng_pool.max_change", 0.25, "%", "A", "model",
     "ten LNG pool trials, LFL distance, **legacy water backend**", "42",
     "the published dense-gas validation runs on LegacyThermo with the legacy "
     "water backend, which extrapolates Antoine below the triple point rather "
     "than clamping. **The correction does not reach that path at all** -- "
     "with_sublimation returns it unchanged, so the change is 0, and the "
     "0.25 % was the wrapper applied to a backend that did not need it"),
    ("lfl.unchanged_by_upstream_fix", True, "-", "A", "model",
     "the full FFI set on slabx 1.0.4 and 1.0.6", "42",
     "**every LFL distance is identical to two decimals** on both, and so "
     "are the verdicts and the required factor of 1.1138. slabx_lh2 supplies "
     "the correction on 1.0.4 and stands aside on 1.0.6, and the answer does "
     "not depend on which"),
    ("defect.lng_with_coolprop_water", 13.8, "%", "A", "model",
     "Burro 8, LFL distance, CoolProp water backend", "42",
     "**the defect is not specific to hydrogen.** Burro 8's cloud runs 208 "
     "to 290 K and 25 of 58 trajectory points are below the water triple "
     "point. Any cryogenic release into humid air that reaches a real-fluid "
     "library for water is affected at this scale"),
    ("slabx.water_fix_upstream", "1.0.6", "-", "-", "measurement",
     "PyPI slabx 1.0.6, thermo/coolprop.py", "42",
     "the correction was adopted upstream: _sublimation_pressure with the "
     "IAPWS coefficients and _H_FUSION = {water: 333400}. slabx_lh2's "
     "water_ice is redundant against 1.0.6 and detects it behaviourally"),
    ("negctl.lng_pool.max_change.withdrawn", 0.37, "%", "-", "withdrawn",
     "hand calculation during the session", "26",
     "superseded by the generated 0.25 %"),
    ("negctl.burro8.change", 0.27, "%", "A", "model",
     "Burro 8, LFL distance", "24", ""),
    ("negctl.prairie_grass", "bit-identical", "-", "A", "model",
     "Prairie Grass, passive SO2", "24", "both modules active"),
    ("negctl.ammonia.change", 0.0, "%", "A", "model",
     "Desert Tortoise-like ammonia pool", "23", "T_min 266 K, above the "
     "water triple point, so the sublimation curve is never reached"),

    # ------------------------------------------------------------ pool radius
    ("pool.radius.median_ratio", 1.03, "-", "B", "comparison",
     "six reported pool radii", "24, 26",
     "USE THIS. Excludes NASA, whose pool was confined by the pond walls"),
    ("pool.radius.median_ratio.with_nasa", 1.11, "-", "C", "comparison",
     "seven radii including NASA", "24",
     "document 24 quotes this; prefer 1.03 and footnote NASA"),
    ("pool.regression.literature", 1.0, "mm/s", "-", "measurement",
     "Takeno 1994, Bailey 1960, ISO TR 15916 B.1", "28", ""),
    ("pool.regression.e34_measured_min", 0.54, "mm/s", "B", "measurement",
     "PRESLHY E3.4 Table 3, fourth period", "28", ""),
    ("pool.regression.e34_measured_max", 0.90, "mm/s", "B", "measurement",
     "PRESLHY E3.4 Table 3, first period", "28", ""),
    ("pool.radius.sensitivity_to_E", "0.67 to 0.91 m", "-", "C", "model",
     "E3.5 trial 7, E from 1.0 to 0.54 mm/s", "28",
     "observed 0.70 m; E is a choice and this is how much it matters"),
    ("pool.boiling_density", 59.2, "kg/m3", "B", "measurement",
     "PRESLHY E3.4, from mass and level", "28",
     "17 % void; pool.py still uses the liquid density 70.8 and is "
     "therefore about 20 % high in the flux conversion"),

    # ------------------------------------------------------- ground conduction
    ("ground.e34.median_ratio", 1.31, "-", "B", "comparison",
     "PRESLHY E3.4 Table 3, four periods", "28",
     "concrete only, on windows the report chose; see docs/29 for the full "
     "set"),
    ("ground.e34.full.concrete02", 1.18, "-", "B", "comparison",
     "E3.4 raw data, 42 rate points", "29", "no wind"),
    ("ground.e34.full.concrete03", 2.73, "-", "B", "comparison",
     "E3.4 raw data, 77 rate points", "29", "side wind 4 m/s"),
    ("ground.e34.full.sand02", 0.25, "-", "B", "comparison",
     "E3.4 raw data, 76 rate points", "29", ""),
    ("ground.e34.full.sand03", 0.31, "-", "B", "comparison",
     "E3.4 raw data, 94 rate points", "29", ""),
    ("ground.e34.depth_drift", 4.3, "-", "A", "diagnostic",
     "erfc inversion at 4 to 54 mm", "29",
     "the box is 100 mm on Styrofoam and is not semi-infinite"),
    ("ground.rr986.depth_drift", 1.8, "-", "A", "diagnostic",
     "erfc inversion at 10 to 30 mm", "33",
     "an outdoor slab; confirms the attribution of the E3.4 drift"),
    ("ground.rr986.alpha_vs_model_min", 2.82, "-", "B", "comparison",
     "RR986 Figure 15, 10 mm", "33", ""),
    ("ground.rr986.alpha_vs_model_max", 5.04, "-", "B", "comparison",
     "RR986 Figure 15, 20 mm", "33", ""),
    ("ground.rr986.temperature_bias", 37.4, "K", "B", "comparison",
     "RR986 Figure 15, 29 points", "33",
     "digitising uncertainty is 5 K; the properties do not transfer"),
    ("ground.concrete.alpha_e34", 2.5e-7, "m2/s", "B", "measurement",
     "PRESLHY E3.4 thermocouples", "28",
     "cryogenic; room-temperature concrete is 6.6e-7"),
    ("ground.concrete.alpha_warm", 6.6e-7, "m2/s", "-", "measurement",
     "room-temperature handbook value", "28",
     "using this under a cryogenic pool halves the heat flux"),
    ("ground.critical_heat_flux", 120e3, "W/m2", "-", "measurement",
     "Shirai et al., Cryogenics 50 (2010) 410", "28",
     "caps the conduction solution for the first 24 s"),
    ("ground.chf.max_rate", 67.4, "g/s", "A", "model",
     "A x CHF / dh_vap", "28", "PRESLHY report 66.8"),
    ("ground.chf.binding_time", 24.3, "s", "A", "model",
     "when conduction falls below the CHF", "28", "PRESLHY report 24.1"),
    ("ground.flux_vs_literature.withdrawn", 0.97, "-", "-", "withdrawn",
     "warm properties at an arbitrary t = 60 s", "28",
     "THE 97 %. There is no single ratio; it runs 2.48 to 0.68 over 60 to "
     "800 s with the correct properties"),

    # -------------------------------------------------------------- the rise
    ("rise.exponent.baseline", 1.28, "-", "A", "model",
     "NASA Test 6, no corrections", "27",
     "range 1.23 to 1.34 over the four trials"),
    ("rise.exponent.width_only", 1.07, "-", "A", "model",
     "NASA Test 6, width coupling", "27", "range 1.05 to 1.28"),
    ("rise.exponent.both", 1.05, "-", "A", "model",
     "NASA Test 6, width coupling and drag", "31",
     "range 0.86 to 1.30 after the aspect-ratio correction"),
    ("rise.exponent.briggs", 0.667, "-", "-", "measurement",
     "Briggs bent-over plume", "22", "the target"),
    ("rise.exponent.registered_band", "0.6 to 0.9", "-", "-", "model",
     "PREREG_lh2_plume_width P-W1", "prereg", ""),
    ("rise.P_W1_pass", 1, "of 4", "A", "comparison",
     "NASA, both corrections, corrected aspect ratio", "31",
     "was 0/4 before the correction; the earlier 'within half a per cent' "
     "was a factor-of-two error"),
    ("rise.exponent.withdrawn_0869", 0.869, "-", "-", "withdrawn",
     "NASA Test 6 before the water correction", "27",
     "the original P-W1 pass; withdrawn, the water fix moves it to 1.047"),
    ("rise.residual.dlnB_dlnz", "0.39 to 0.59", "-", "A", "diagnostic",
     "NASA four trials, both corrections", "27",
     "Briggs needs 1.0; the width is coupled only partway"),
    ("rise.residual.dlnh_dlnz", "0.23 to 0.49", "-", "A", "diagnostic",
     "NASA four trials", "27",
     "Briggs needs 1.0; **the depth is not coupled to the rise at all**"),
    ("rise.residual.prediction_accuracy", 0.059, "fraction", "A",
     "diagnostic", "n = 2/(s+1) against the fitted exponent", "27",
     "worst of the four; the set is 3.0, 3.1, 5.7 and 5.9 %. This is what "
     "turns a failure into a located missing term"),
    ("drag.cd0_continuous", 1.17, "-", "-", "measurement",
     "circular cylinder in crossflow, classical", "31", "not fitted"),
    ("drag.cd1_continuous", 1.2, "-", "-", "measurement",
     "aspect-ratio dependence, numerical", "31", "not fitted"),

    # --------------------------------------------------------------- premise
    ("premise.ffi.max_ratio", 0.182, "-", "A", "diagnostic",
     "six FFI trials", "22", "range 0.048 to 0.182; all inside"),
    ("premise.e35.max_ratio", 0.697, "-", "A", "diagnostic",
     "seventeen E3.5 trials", "27", "range 0.015 to 0.697; all inside"),
    ("premise.nasa.max_ratio", 4.74, "-", "A", "diagnostic",
     "four NASA trials", "31", "range 0.61 to 4.74; three of four outside"),
    ("premise.zhang.max_ratio", 821.8, "-", "A", "diagnostic",
     "eight Zhang trials", "27", "range 13.7 to 821.8; all outside"),
    ("premise.nasa.rise_angle", 75.0, "deg", "A", "diagnostic",
     "NASA Test 6", "22", "the cloud rises at 75 degrees while the "
     "formulation integrates downwind"),
    ("premise.zhang.rise_angle", "85.8 to 89.9", "deg", "A", "diagnostic",
     "eight Zhang trials", "27",
     "the failure is visible, which is the property the monitoring "
     "application depends on"),
    ("ucrit.D.a", 2.674, "-", "A", "model",
     "bisected on max w_c/u, fitted log-log", "30", ""),
    ("ucrit.D.b", 0.135, "-", "A", "model", "as above", "30", ""),
    ("ucrit.fit_range", "0.1 to 30", "kg/s", "-", "model", "as above", "30",
     "outside this it is extrapolation"),
    ("ucrit.withdrawn", "2.5 q^0.15", "-", "-", "withdrawn",
     "a round figure in document 22", "30",
     "agrees with the fit to 3 % but is not what critical_wind uses"),
    ("ucrit.screening_vs_diagnostic", "28 of 35 agree", "-", "A",
     "diagnostic", "four campaigns, scripts/applicability_all.py", "37",
     "seven disagreements, all momentum jets that the pool-fitted screen "
     "flags conservatively"),
    ("ucrit.screening_misses", 0, "cases", "A", "diagnostic",
     "four campaigns, n = 35", "37",
     "**no case that the model refuses was passed by the screen.** A false "
     "flag costs one unnecessary integration; a miss would let a caller use "
     "a number the model does not stand behind"),
    ("ucrit.agreement_on_pools", "15 of 15", "-", "A", "diagnostic",
     "NASA, Zhang, E3.5 downward", "37",
     "the screen was fitted to a pool source, so this is the case it should "
     "get right; every disagreement is a jet"),
    ("runtime.warm_e2e_p95_ffi4", 94.8, "ms", "-", "model",
     "scripts/benchmark_runtime.py, n = 40", "37",
     "inputs to source and atmosphere to model to premise to LFL to result. "
     "Hardware-specific; regenerate before quoting"),
    ("runtime.warm_e2e_p95_out_of_scope", 206.9, "ms", "-", "model",
     "NASA Test 6, n = 40", "37",
     "refusing costs a full integration, and is the slowest case"),
    ("runtime.batch_p95_ffi6", 625.4, "ms", "-", "model",
     "six FFI trials in one process, n = 12", "37", ""),
    ("runtime.cold_start_p50", 3413.6, "ms", "-", "model",
     "fresh interpreter, n = 6", "37",
     "**38 times the warm figure**; a per-request subprocess is not viable "
     "and the worker pool has to be processes, not threads, because of the "
     "global patch"),
    ("ablation.ffi_driver", "water correction", "-", "A", "diagnostic",
     "2x2, scripts/ablation_2x2.py", "37",
     "W0C0 = W0C1 and W1C0 = W1C1 on FFI: the coupling is gated on is_lofted "
     "and no FFI trial lofts. Tests 1 and 6 move from outside the bracket to "
     "inside on the water correction alone"),
    ("ablation.nasa_driver", "width coupling", "-", "A", "diagnostic",
     "2x2 rise exponent", "37",
     "water alone raises the exponent 1.19 to 1.28, the coupling alone drops "
     "it to 0.89, and together they partly cancel at 1.05"),

    # ------------------------------------------------------------- lift-off
    ("briggs.threshold", 20.0, "-", "-", "measurement",
     "Briggs 1973", "prereg", "stated uncertainty a factor of two"),
    ("briggs.ffi.lifted", 29.0, "-", "C", "comparison",
     "FFI Test 6", "prereg", "the rest are 2.3 to 11.7"),
    ("briggs.e35.rank_corr_wind", -0.891, "-", "C", "comparison",
     "seventeen E3.5 trials", "prereg", ""),
    ("briggs.e35.rank_corr_rate", 0.213, "-", "C", "comparison",
     "seventeen E3.5 trials", "prereg",
     "the point: L_p sorts by wind, not by release rate"),
    ("briggs.e35.rank_corr_wind.robustness", "-0.891 to -0.936", "-", "C",
     "comparison", "three flow-rate bases: nominal, meter peak, meter mean",
     "36",
     "the rate spans 14 to 298 g/s across the three and the ordering does not "
     "move; the rate correlation stays at +0.20 to +0.31"),
    ("ffi.test5.duration", 240.0, "s", "-", "measurement",
     "FFI-RAPPORT 20/03101 section 2.3.5", "36",
     "two minutes unignited, a valve closure, two more unignited, then "
     "ignition. Not the 360 s run time and not the 120 s first release, "
     "which is what this work used until the pre-submission audit"),
    ("ffi.test5.duration.withdrawn", 120.0, "s", "-", "withdrawn",
     "the first unignited release only", "36",
     "replaced by 240 s; the LFL distance moves 45.75 to 43.56 m and no "
     "verdict changes"),
    ("briggs.nasa.rank_corr_wind", -1.0, "-", "C", "comparison",
     "four NASA trials", "prereg", ""),
    ("briggs.rr986.transition", "2.7 to 2.9", "m/s", "C", "comparison",
     "four RR986 trials at fixed 60 L/min", "prereg",
     "RR986's own text says the cloud was more buoyant below 3 m/s"),
    ("briggs.threshold_transfers", False, "-", "C", "comparison",
     "four campaigns", "prereg",
     "separates three sets spanning 0.07 to 0.83 kg/s and fails on NASA at "
     "10 to 17; carried as an ordering variable, not a gate"),

    # ------------------------------------------------------------------ LFL
    ("lfl.in_bracket", 5, "of 6", "B", "comparison",
     "FFI arcs at 30, 50 and 100 m", "24, 27", ""),
    ("lfl.safety_factor_required", 1.114, "-", "B", "comparison",
     "the six FFI trials", "27",
     "REPLACES 1.23, which came from the un-interpolated grid"),
    ("lfl.safety_factor_required.withdrawn", 1.23, "-", "-", "withdrawn",
     "before the crossing was interpolated", "27",
     "replaced by 1.114. slabx integrates on a geometric grid and the "
     "distance was read at the last node above the limit rather than at the "
     "interpolated crossing, which made four trials return an identical "
     "40.75 m"),
    ("lfl.safety_factor_adopted", 1.25, "-", "-", "model",
     "rounded engineering margin", "26",
     "derived and evaluated on the same six trials; **not independently "
     "validated**"),
    ("lfl.phmsa_lng_factor", 2.5, "-", "-", "measurement",
     "PHMSA, LNG in stable low wind", "24", "for comparison"),
    ("lfl.grid_independence", 0.001, "fraction", "A", "model",
     "x_max from 120 to 1200 m", "27",
     "after interpolation; before it, four trials returned an identical "
     "40.75 m because the geometric grid is shared"),
    ("lfl.humidity_insensitivity", 1.3, "-", "A", "model",
     "RH 60, 75 and 90 %", "27",
     "the ratio of the largest to the smallest LFL distance; the arc "
     "concentrations move by an order of magnitude over the same sweep"),

    # ------------------------------------------------------- air condensation
    ("air.onset.N2", 90.27, "mol%", "A", "model",
     "adiabatic mix with sublimation below the triple points", "30", ""),
    ("air.onset.O2", 88.15, "mol%", "A", "model", "as above", "30", ""),
    ("air.ufl_hydrogen", 75.0, "mol%", "-", "measurement", "standard", "30",
     "onset is above it, so air condensation never happens inside the "
     "flammable range"),
    ("air.effect_direction", "lighter", "-", "A", "model",
     "rho/rho_a 0.883 to 0.729 at 97 mol%", "30",
     "latent heat and the loss of heavy species both lower the density"),

    # -------------------------------------------------- orientation / sources
    ("orientation.measured_ratio", 2.69, "-", "C", "measurement",
     "FFI Test 4 / Test 3 at 30 m", "18",
     "matched rate, pressure and nozzle; differ in orientation"),
    ("orientation.slabx_ratio", 1.03, "-", "A", "model",
     "same pair, both as HorizontalJet", "18", ""),
    ("orientation.chen_rodi_ratio", 1.0, "-", "A", "comparison",
     "Chen & Rodi similarity law on the same pair", "22",
     "**the reference correlation cannot distinguish them either**"),
    ("orientation.pool_source_ratio", 13684.0, "-", "A", "model",
     "vertical-down as a momentumless pool", "prereg",
     "the rejected ImpingingJet; the measurement is bracketed by four "
     "orders of magnitude"),
    ("orientation.misreading", "horizontal under-predicted", "-", "B",
     "diagnostic", "FFI Tests 3, 4, 7 at 30 m", "prereg",
     "document 18 read this backwards: vertical-down is already right and "
     "the horizontal case is 2.6x low"),

    # ------------------------------------------------------------ hyram, cfd
    ("hyram.trials_run", "1 of 4", "-", "C", "comparison",
     "FFI outdoor trials", "18",
     "HyRAM+ 6.1 has no ground boundary, so vertical-down releases pass "
     "through the ground"),
    ("hyram.cloud_height_at_100m", 99.9, "m", "C", "comparison",
     "FFI Test 4", "18", "slabx 1.83 m, measured 1.8 m"),
    ("effects.max_underprediction", "reported", "-", "-", "measurement",
     "Mack & Boot, ICHS 2023", "27",
     "a mature commercial integral model reports the same "
     "under-prediction of maxima; not a slabx-specific defect"),

    # ------------------------------------------------------- repeatability
    ("repeatability.ffi.max_concentration", 0.22, "fraction", "B",
     "measurement", "FFI Tests 3 and 5", "27",
     "a near-repeat pair: 2 % apart in rate and 10 % in wind, and the "
     "measured maxima differ by this much"),
    ("repeatability.ffi.peak_height_flips", True, "-", "B", "measurement",
     "FFI Tests 3 and 5", "27",
     "0.1 m in one, 1.0 and 1.8 m in the other; **the vertical peak height "
     "cannot be a decision variable on this data**"),
    ("repeatability.rr986.pool_radius", 0.36, "fraction", "B", "measurement",
     "RR986 Tests 5 and 6 at the same rate", "28",
     "0.83 and 1.13 m equivalent radius"),

    # ------------------------------------------------------------ provenance
    ("provenance.ffi.humidity", "not reported", "-", "-", "measurement",
     "FFI-RAPPORT 20/03101 weather tables", "27",
     "measured by DNV but not tabulated in the public report; every FFI run "
     "here assumes a value, and the arc statistics swing from FAC2 0.42 to "
     "0.92 across a plausible range"),
    ("provenance.nasa.vertical_lfl", "second-hand", "-", "-", "measurement",
     "EFFECTS Table 3, citing an unobtained source", "27",
     "53, 27, 65 and 9 m; a different quantity from Witcofski Table 4's "
     "minimum heights, and the conditions differ between three sources"),
    ("provenance.nasa.detachment.withdrawn", "20 m", "-", "-", "withdrawn",
     "Ichard et al. reading a contour plot", "27",
     "the original reports ground-level travel of 50 to 100 m; two "
     "different measurements"),
    ("adrea.hsl5.MG_no_humidity", 0.22, "-", "C", "measurement",
     "Giannissi et al., ICHS 2011, Table 2", "36",
     "ADREA-HF against HSL Test 5 sensor concentrations; MG below 1 is "
     "under-prediction, which the authors state"),
    ("adrea.hsl5.MG_with_humidity", 0.84, "-", "C", "measurement",
     "Giannissi et al., ICHS 2011, Table 2", "36", "ln(VG) 12.18 to 4.7"),
    ("adrea.lfl_reduction_from_humidity", 0.40, "fraction", "C",
     "measurement", "Giannissi et al., ICHS 2011, conclusions", "36",
     "with humidity the LFL distance falls to about 40 % of the dry case "
     "early in the release; humidity is the first-order variable"),
    ("effects.nasa.horizontal_lfl_error", "-20 to +33 %", "-", "C",
     "measurement", "Mack & Boot JLP 2023, Table 3", "36", ""),
    ("effects.nasa.vertical_lfl_error", "-28 to 0 %", "-", "C",
     "measurement", "Mack & Boot JLP 2023, Table 3", "36",
     "the two worst are the two outside the bent-over premise; see docs/35"),
    ("comparison.not_possible", "different targets, rates, gaps", "-", "-",
     "diagnostic", "docs/36 section 36.3", "36",
     "concentrations vs LFL distance, 0.07 to 10.3 kg/s, and each dataset "
     "missing a different input; a single performance table would be false"),
    ("slabx.buoyant_branch_exists", True, "-", "A", "measurement",
     "core/plume.py is_lofted, EQ 6a branch", "38",
     "**the branch is there.** The problem is that the rise is unbounded, "
     "not that it is absent; a feature table marking it as missing repeats "
     "error 9 of section C7a"),
    ("slabx.flash_is_an_input", True, "-", "A", "measurement",
     "core/source.py line 420", "38",
     "liquid_fraction is supplied, not solved; this work computes it "
     "externally with a CoolProp isenthalpic flash"),
    ("hyram.no_ground_boundary", True, "-", "B", "measurement",
     "HyRAM+ 6.1 run directly on the FFI trials", "38",
     "downward releases pass through the ground, so three of four could not "
     "be run at all"),
    ("degadis.core_is_momentumless", True, "-", "-", "measurement",
     "EPA Science Inventory record for DEGADIS", "39",
     "ground-level low-momentum area sources, negatively and neutrally "
     "buoyant; jets come from a separate Ooms/JETPLUME front end"),
    ("degadis.aerosol_density_is_user_supplied", True, "-", "-",
     "measurement", "EPA record", "39",
     "the model does not characterise the density of aerosol releases"),
    ("degadis.regulatory_designation", "49 CFR 193.2059", "-", "-",
     "measurement", "GTI distribution note", "39",
     "confirms error 6 of section C7a: this work once wrote that SLAB is the "
     "regulatory model, and DEGADIS is"),
    ("hgsystem.aeroplume_does_buoyant_jets", True, "-", "-", "measurement",
     "HGSYSTEM AEROPLUME user guide", "39",
     "dense, neutral and buoyant jets at arbitrary release angle; the "
     "technical manual adds plume rise, fall and touchdown"),
    ("hgsystem.has_liftoff", True, "-", "-", "measurement",
     "Witlox HGSYSTEM/UF6 enhancements", "39",
     "buoyant plume lift-off against wind tunnel data; **so lift-off is not "
     "novel**"),
    ("comparison.buoyant_rise_is_common", True, "-", "-", "diagnostic",
     "six models surveyed", "39",
     "only the DEGADIS core and the HEGADAS module lack it, and both get it "
     "from a front-end model. Adding buoyant rise is not the contribution; "
     "knowing when it may not be used is"),
    ("comparison.phast_udm", "unverified", "-", "-", "measurement",
     "commercial; manual not obtained", "39",
     "its FFI predictions are in DNV GL 853182, which is not public"),
    ("effects.slab_lineage", "cites Ermak 1990", "-", "-", "measurement",
     "Mack & Boot JLP 2023, reference [13]", "35",
     "their vertical entrainment reproduces SLAB EQ 35a including the sqrt3 "
     "and a = 1.5, so the premise diagnosis applies to them as well"),
    ("effects.validation_outside_premise", "3 of 6", "-", "A", "diagnostic",
     "EFFECTS Table 2 conditions, run through premise_summary", "35",
     "max w_c/u of 4.90, 2.93 and 1.76 on tests 2, 6 and 4"),
    ("effects.vertical_lfl_error.outside", "-26 and -28 %", "-", "C",
     "comparison", "EFFECTS Table 3, tests 6 and 4", "35",
     "against 0 and -15 % on the two inside; n = 4, a direction not a "
     "correlation"),
    ("nasa.pond_radius", 4.55, "m", "-", "measurement",
     "Witcofski & Chirivella 1984, 9.1 m diameter pond", "35", "first-hand"),
    ("nasa.pool_radius.second_hand", "2 to 3", "m", "C", "measurement",
     "EFFECTS, citing observation", "35",
     "**the original does not report it**; the plume-width result depends on "
     "which is used and this one was found after seeing the failure"),
    ("rise.P_W1.source_term_sensitivity", "FAIL to PASS", "-", "-",
     "diagnostic", "NASA Test 6, pond 4.55 m vs pool 3 m", "35",
     "n goes 1.068 to 0.877; **not recorded as a pass**, because the input "
     "that decides it is not in the first-hand record"),
    ("provenance.bam.rate", "three sources, three values", "-", "-",
     "measurement", "0.4, 0.37 and 0.8 kg/s", "docs/README", "unusable"),
]


def main() -> int:
    out = []
    for key, value, unit, grade, kind, source, doc, note in RECORDS:
        out.append({"key": key, "value": value, "unit": unit, "grade": grade,
                    "kind": kind, "source": source, "doc": doc, "note": note})

    seen = set()
    for r in out:
        if r["key"] in seen:
            raise SystemExit(f"duplicate key: {r['key']}")
        seen.add(r["key"])

    data = ROOT / "data"
    (data / "catalogue.json").write_text(
        json.dumps({"grades": GRADES, "records": out}, indent=2,
                   ensure_ascii=False), encoding="utf-8")
    with (data / "catalogue.csv").open("w", newline="",
                                       encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)

    by_kind: dict[str, int] = {}
    by_grade: dict[str, int] = {}
    for r in out:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
        by_grade[r["grade"]] = by_grade.get(r["grade"], 0) + 1
    print(f"wrote {len(out)} records to data/catalogue.{{json,csv}}")
    print("  by kind :", ", ".join(f"{k} {v}" for k, v in
                                   sorted(by_kind.items())))
    print("  by grade:", ", ".join(f"{k} {v}" for k, v in
                                   sorted(by_grade.items())))
    n = by_kind.get("withdrawn", 0)
    print(f"\n  {n} withdrawn values are recorded so that a reader who finds "
          f"one\n  in an old draft can look it up. They must not be quoted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
