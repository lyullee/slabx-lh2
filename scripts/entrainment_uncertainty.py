"""
How much air the formulation entrains at 30 m, and what that rests on.

    python scripts/entrainment_uncertainty.py

Writes `paper_results/entrainment_uncertainty.csv`.

The model side
--------------
**`Trajectory.R_flux` is a half-plume flux.** SLAB integrates one side of a
symmetric cloud, so `2 * R_flux` is the total. This is checked at the source
in `TestRFluxIsAHalfFlux`: `2 * R_flux[0]` equals the release rate to twelve
figures on every FFI trial.

An earlier version of this script read `R_flux` as the total and reported
half the true excess. **That number is withdrawn.**

The measurement side
--------------------
The entrained mass is not measured. It is inferred from a temporal maximum on
a polar sensor arc, while the mass balance needs a cross-sectional mean on a
fixed downwind plane. The available data do not provide that conversion; see
``sensor_audit.py``.

Nothing else in the inference is free. The hydrogen flux is the release rate,
so

    total flux = release rate / w_H2,    w_H2 from the bulk mole fraction

and the advection speed, the cross-sectional area and the mixture density all
cancel: the dilution fixes the total flux whatever speed the cloud moves at.
An earlier version varied those as if they were independent; they are not.

Two illustrative assumptions, not bounds
-----------------------------------------
The conversion is shown as two explicit assumptions only:

    bulk = 0.5 * peak    an illustrative half-peak conversion
    bulk = peak          an extreme equality assumption

Neither is measured, and neither is assigned a probability. In particular,
``bulk = peak`` minimises the inferred flux and therefore *maximises* the
model/inferred ratio; it is not a lower bound on excess. Report the model flux
as the result and these ratios, if retained at all, as conditional diagnostics.
"""

from __future__ import annotations

import argparse
import csv
import warnings
from pathlib import Path

import numpy as np

warnings.simplefilter("ignore")

from slabx.core.plume import run_dispersion                      # noqa: E402
from slabx.core.source import HorizontalJet                      # noqa: E402
from slabx.submodels.atmosphere import Atmosphere                # noqa: E402
from slabx.thermo.base import Substance                          # noqa: E402
from slabx.thermo.coolprop import CoolPropThermo, coolprop_water  # noqa: E402

from slabx_lh2.plume_width import plume_width_coupling           # noqa: E402
from slabx_lh2.trials import FFI                                 # noqa: E402
from slabx_lh2.trials import observations as OB                  # noqa: E402
from slabx_lh2.water_ice import with_sublimation                 # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
H2 = Substance(name="H2", mw=0.002016, cp_vapour=14300., cp_liquid=9800.,
               dh_vap=445000., T_boil=20.3, rho_liquid=70.8)
MW_H2, MW_AIR = 2.016, 28.96
ARC = 30.0
#: bulk / peak, and what each assumes.
SCENARIOS = {
    "half_peak_illustrative": (
        0.5, "illustrative only; the polar arc and temporal statistic do not "
             "identify a fixed-x cross-sectional mean"),
    "peak_equals_bulk_extreme": (
        1.0, "extreme equality assumption; minimises inferred flux and "
             "maximises the conditional model/inferred ratio"),
}


def total_flux(traj, x: float) -> float:
    """
    Total mass flux [kg/s] at `x`.

    **`R_flux` is a half-plume flux** -- SLAB integrates one side of a
    symmetric cloud. `2 * R_flux[0]` equals the release rate exactly.
    """
    return 2.0 * float(np.interp(x, np.asarray(traj.x),
                                 np.asarray(traj.R_flux)))


def inferred_flux(peak_vol_frac: float, rate_kg_s: float,
                  bulk_over_peak: float) -> float:
    """Total mass flux the arc reading implies [kg/s]."""
    bulk = min(max(peak_vol_frac * bulk_over_peak, 1e-9), 0.999)
    w_h2 = bulk * MW_H2 / (bulk * MW_H2 + (1.0 - bulk) * MW_AIR)
    return rate_kg_s / w_h2


def run_trial(trial: int, humidity_pct: float = 75.0):
    t = FFI[trial]
    atm = Atmosphere(u_ref=t.wind_m_s, z_ref=10.0,
                     T=t.temperature_C + 273.15, rh=humidity_pct, z0=0.01,
                     stability="D")
    src = HorizontalJet(substance=H2, rate=t.rate_kg_s, area=t.area_m2,
                        duration=t.duration_s,
                        liquid_fraction=t.liquid_fraction,
                        height=t.release_height_m, T_source=20.37)
    with plume_width_coupling():
        traj, _ = run_dispersion(src, atm,
                                 CoolPropThermo(H2, fluid="Hydrogen"),
                                 with_sublimation(coolprop_water()),
                                 x_max=200.0, n_puff_steps=40)
    return traj, t


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="paper_results")
    ap.add_argument("--trials", type=int, nargs="*", default=[4, 6])
    args = ap.parse_args()

    try:
        {t: OB.arc_maxima(t) for t in args.trials}
    except OB.ObservationsUnavailable as exc:
        print(exc)
        return 0

    rows = []
    print("Model flux at 30 m and two conditional concentration conversions\n")
    for trial in args.trials:
        peak_pct = OB.arc_maxima(trial)[0]
        traj, t = run_trial(trial)
        r0 = 2.0 * float(np.asarray(traj.R_flux)[0])
        model = total_flux(traj, ARC)
        print(f"Test {trial}   u = {t.wind_m_s} m/s, q = {t.rate_kg_s} kg/s, "
              f"30 m maximum {peak_pct:.1f} vol %")
        print(f"  source check   2 x R_flux[0] = {r0:.6f} kg/s   "
              f"against the release rate {t.rate_kg_s:.6f}")
        print(f"  model total flux at 30 m        {model:9.3f} kg/s   "
              f"(exact, no assumption)")
        for name, (bop, why) in SCENARIOS.items():
            inf = inferred_flux(peak_pct / 100.0, t.rate_kg_s, bop)
            ratio = model / inf
            print(f"  {name:>14}  bulk/peak {bop:.1f}   "
                  f"inferred {inf:8.3f} kg/s   -> **{ratio:.3f}**")
            rows.append({"trial": trial, "scenario": name,
                         "bulk_over_peak": bop, "peak_vol_pct": peak_pct,
                         "model_total_flux_kg_s": model,
                         "inferred_flux_kg_s": inf,
                         "model_over_inferred_flux": ratio,
                         "rationale": why})
        print()

    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    with (out / "entrainment_uncertainty.csv").open(
            "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print("The model total flux is the only assumption-free result here. "
          "Do not average the two conditional ratios, present them as a "
          "range, or call either one a measured bound.")
    print(f"\nwrote {out / 'entrainment_uncertainty.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
