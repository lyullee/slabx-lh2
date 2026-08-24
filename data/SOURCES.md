# Where the measurements come from

This package ships **trial conditions** and not **trial measurements**. The
conditions are the experiments' settings and nobody can run the model without
them; the measurements are the reports' findings, and redistributing those is
the originating organisation's decision rather than this project's.

Nothing below is secret. Four of the five sets are free, and
`scripts/extract/` turns each report back into exactly the CSV this work used.

> **What you lose without them:** the comparisons against measurement — the
> LFL bracket verdicts, the pool radii, the RR986 temperature field. Grade B
> and C in `data/catalogue.csv`.
>
> **What still works:** every model output and internal comparison. The
> water-saturation defect, the dense-gas negative controls, the applicability
> diagnostic and its screening curve, the runtime benchmark, the 2x2 ablation,
> the applicability map. Those are grade A and they carry the two main claims.
>
> `docs/40_PUBLIC_RELEASE.md` lists which result falls on which side.

---

## FFI outdoor trials, Spadeadam 2019

| | |
|---|---|
| report | Aaneby, Gjesdal & Voie (2020), *Large scale leakage of liquid hydrogen*, FFI-RAPPORT 20/03101 |
| access | public PDF, FFI (Norwegian Defence Research Establishment) |
| extract | `python scripts/extract/parse_ffi.py <report.pdf>` |
| gives | `lh2_ffi_sensors.csv` (826 rows), `lh2_ffi_conditions.csv` (7) |

Appendix A carries per-sensor maxima and means on the 30, 50 and 100 m arcs at
0, 0.1, 1.0 and 1.8 m height.

**Humidity is not in this report.** It was measured by DNV and appears in
DNV GL 853182 Rev.2, which is not public. Every FFI run here assumes a value.
The arc statistics swing from FAC2 0.42 to 0.92 across 60 to 90 % RH; the LFL
distance does not move, which is why this work decides on the distance.

## PRESLHY E3.5, far-field dispersion

| | |
|---|---|
| dataset | DOI 10.35097/1481, KITopen |
| licence | **CC BY-SA 4.0** |
| extract | `python scripts/extract/extract_e35_v2.py <folder>` |
| gives | `lh2_e35_farfield_v2.csv` (686), `lh2_e35_conditions_v2.csv` (24) |

**The Dräger sensors saturate at 4 vol%.** 57 of 686 rows sit at the ceiling;
the `saturated` column marks them and they must be excluded from any
concentration statistic.

The conditions sheet records a flow meter as well as the nominal table rate.
Peak and mean differ from the table by up to 30 % and 60 %; the Briggs
ordering is insensitive to which is used (-0.891 to -0.936 across all three).

## PRESLHY E3.4, unignited pool experiments

| | |
|---|---|
| dataset | DOI 10.35097/1319, KITopen (registration required) |
| report | PRESLHY D3.5, *Summary of experiment series E3.4 (POOL-Facility)* |
| extract | `python scripts/extract/extract_e34.py <folder>` |
| gives | `lh2_e34_rates.csv` (289), `lh2_e34_traces.csv` (1754), `lh2_e34_summary.csv` (5) |

Ten 16 to 90 MB spreadsheets, of which five are usable: `Concrete01` has no
scale record and the three `Gravel` runs have a weight signal the report itself
says cannot be used, because frozen air accumulates in the porous bed.

**Table 3 is on `Orig.Time`, the scale's own clock**, which runs 7.67 s behind
the synchronised column. The fills are 30 s long, so reading the wrong clock
moves the rates by tens of per cent.

**The box is 100 mm deep on Styrofoam and is not a semi-infinite solid.**
Inverting the erfc solution at 4, 9, 14, 54 and 98 mm gives diffusivities that
drift by a factor of four with depth. See `docs/29_E34_FULL.md`.

## HSE RR986

| | |
|---|---|
| report | Royle & Willoughby (2014), *Experimental releases of liquid hydrogen*, RR986 |
| access | public PDF, Health and Safety Executive |
| extract | figure 15 digitised by hand; the values are in `scripts/rr986_ground.py` |
| gives | concrete temperatures at 10, 20 and 30 mm, about ±5 K and ±5 s |

**The embedded thermocouples read 233 K before the release** against a
reported ambient of 283.5 K. Whether that is a calibration offset — PRESLHY
found a 43.5 K one on the same kind of probe — or concrete left cold by an
earlier run cannot be settled from the figure, so `T_0` is taken from each
trace's own plateau.

## NASA White Sands

| | |
|---|---|
| paper | Witcofski & Chirivella (1984), *Int. J. Hydrogen Energy* **9**, 425–435 |
| access | publisher. **The paper states it is a US Government work not subject to copyright** |
| gives | table 1 conditions, tables 3 and 4 concentrations and heights |

**The pool radius is not reported**, only the 9.1 m diameter pond. EFFECTS
cite an observed 2 to 3 m; the rise exponent depends on which is used, and
that dependence is recorded in `docs/35_EFFECTS_COMPARISON.md`.

## Zhang et al. (2024)

| | |
|---|---|
| paper | *Appl. Sci.* **14**, 3645, DOI 10.3390/app14093645 |
| access | open access, MDPI |
| gives | table 1 conditions for twelve trials |

Four of the twelve report no duration and cannot be converted to a rate. The
remaining eight are all below 0.7 m/s wind, which is why they serve as an
out-of-domain stress test rather than a discriminating validation.

---

## Installing them

Put the extracted CSVs in `data/`, or point `SLABX_LH2_DATA` at the directory
holding them:

```bash
export SLABX_LH2_DATA=/path/to/csvs
pytest                      # the skipped comparisons now run
python scripts/reproduce.py --json
```

`slabx_lh2.trials.observations.available(key)` reports what is installed
without raising.
