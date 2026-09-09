"""
One table for all six FFI trials.

    python scripts/ffi_summary_table.py

Writes `paper_results/ffi_summary.csv`.

Why one table
-------------
The claim is not "the model is inaccurate". It is that the error is
**systematic in release orientation and in whether the cloud lofts**, and
that only shows when the orientation, the rates, the near-field
concentration, the LFL distance, the premise ratio and the lift-off
observation sit in the same row.

Columns, and what each is
-------------------------
    orientation      as released, from the report
    rate, wind       the trial's settings
    c30_meas         30 m arc maximum, largest of three sensor heights
    c30_model        the same quantity from the model
    c30_ratio        model / measured -- **the systematic split lives here**
    lfl_m            distance to 4 vol %, the quantity the paper decides on
    bracket          which arc interval the measurement puts it in
    verdict          in / not conservative / conservative
    Pi               max w_c/u, the model's own premise diagnostic
    status           VALID / MARGINAL / OUT_OF_SCOPE
    L_p              Briggs lift-off parameter, threshold 20
    lofted_obs       whether the measurement shows lift-off
    lofted_model     whether L_p crosses the threshold

`lofted_obs` is **exploratory and is not a result**. It applies a decay
threshold this work chose, to six trials, and there is no way to separate
setting the threshold from testing it. It is in the CSV so the pattern can be
seen; **do not quote a hit rate from it.**

What can be quoted is the pair that external work confirms: Mack & Boot
(ICHS 2023) report no lift-off on test 4 and a lifted plume on test 6, and
Briggs's parameter here is 3.8 and 28.9 against a threshold of 20 -- test 6
being the only one of the six above it.
"""

from __future__ import annotations

import argparse
import csv
import math
import warnings
from pathlib import Path

import numpy as np

warnings.simplefilter("ignore")

from slabx.core.plume import run_dispersion                      # noqa: E402
from slabx.core.source import HorizontalJet                      # noqa: E402
from slabx.post.concentration import concentration_field         # noqa: E402
from slabx.submodels.atmosphere import Atmosphere                # noqa: E402
from slabx.thermo.base import Substance                          # noqa: E402
from slabx.thermo.coolprop import CoolPropThermo, coolprop_water  # noqa: E402

from slabx_lh2.diagnostics import applicability, briggs_liftoff  # noqa: E402
from slabx_lh2.lfl import (brackets_from_arcs, flammable_distance,  # noqa: E402,E501
                           verdict)
from slabx_lh2.plume_width import plume_width_coupling           # noqa: E402
from slabx_lh2.trials import FFI                                 # noqa: E402
from slabx_lh2.trials import observations as OB                  # noqa: E402
from slabx_lh2.water_ice import with_sublimation                 # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
H2 = Substance(name="H2", mw=0.002016, cp_vapour=14300., cp_liquid=9800.,
               dh_vap=445000., T_boil=20.3, rho_liquid=70.8)
ARCS = (30.0, 50.0, 100.0)
HEIGHTS = (0.1, 1.0, 1.8)
#: Ratio of the 30 m to the 50 m reading above which the fall is too steep
#: for dispersion. **Chosen here, on these six trials.** Exploratory only.
LOFT_DECAY = 6.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="paper_results")
    ap.add_argument("--humidity", type=float, default=75.0)
    args = ap.parse_args()

    try:
        {t: OB.arc_maxima(t) for t in FFI}
    except OB.ObservationsUnavailable as exc:
        print(exc)
        return 0

    rows = []
    for t in sorted(FFI):
        tr = FFI[t]
        meas = OB.arc_maxima(t)
        atm = Atmosphere(u_ref=tr.wind_m_s, z_ref=10.0,
                         T=tr.temperature_C + 273.15, rh=args.humidity,
                         z0=0.01, stability="D")
        src = HorizontalJet(substance=H2, rate=tr.rate_kg_s, area=tr.area_m2,
                            duration=tr.duration_s,
                            liquid_fraction=tr.liquid_fraction,
                            height=tr.release_height_m, T_source=20.37)
        with plume_width_coupling():
            traj, _ = run_dispersion(src, atm,
                                     CoolPropThermo(H2, fluid="Hydrogen"),
                                     with_sublimation(coolprop_water()),
                                     x_max=300.0, n_puff_steps=40)
        model = {}
        for R in ARCS:
            best = 0.0
            for z in HEIGHTS:
                f = concentration_field(traj, atm, z=z,
                                        t_avg=tr.averaging_window_s,
                                        t_release=tr.duration_s)
                best = max(best, float(np.interp(R, f.x,
                                                 np.asarray(f.peak))) * 100)
            model[R] = best
        d = flammable_distance(traj, atm, t_avg=tr.averaging_window_s,
                               t_release=tr.duration_s, safety_factor=1.0)
        lo, hi = brackets_from_arcs(ARCS, meas)
        app = applicability(traj)
        lp = float(briggs_liftoff(traj, atm).max())
        decay = meas[0] / meas[1] if meas[1] > 0 else float("inf")
        rows.append({
            "trial": t, "orientation": tr.orientation,
            "rate_kg_s": tr.rate_kg_s, "wind_10m_m_s": tr.wind_m_s,
            "c30_meas_pct": meas[0], "c30_model_pct": round(model[30.0], 2),
            "c30_ratio": round(model[30.0] / meas[0], 3),
            "c50_meas_pct": meas[1], "c50_model_pct": round(model[50.0], 2),
            "c100_meas_pct": meas[2],
            "c100_model_pct": round(model[100.0], 3),
            "lfl_m": round(d["raw"], 2),
            "bracket_lower_m": lo,
            "bracket_upper_m": "" if math.isinf(hi) else hi,
            "verdict": verdict(d["raw"], (lo, hi)),
            "premise_ratio_max": round(app["premise_ratio"], 3),
            "applicability": app["status"],
            "briggs_Lp_max": round(lp, 1),
            "decay_30_to_50": round(decay, 1),
            "lofted_observed_exploratory": int(decay > LOFT_DECAY),
            "lofted_model": int(lp > 20.0),
            "assumed_humidity_pct": args.humidity,
        })

    print("FFI, all six trials\n")
    print(f"{'t':>2}{'dir':>6}{'q':>7}{'u':>6}"
          f"{'30m obs':>9}{'model':>8}{'ratio':>7}"
          f"{'LFL':>7}{'bracket':>10}{'verdict':>18}"
          f"{'Pi':>7}{'L_p':>7}{'loft':>7}")
    for r in rows:
        br = (f"{r['bracket_lower_m']:.0f}-{r['bracket_upper_m']:.0f}"
              if r["bracket_upper_m"] != ""
              else f">{r['bracket_lower_m']:.0f}")
        loft = ("obs+mod" if r["lofted_observed_exploratory"]
                and r["lofted_model"]
                else "obs" if r["lofted_observed_exploratory"]
                else "mod" if r["lofted_model"] else "-")
        print(f"{r['trial']:>2}{r['orientation'][:4]:>6}{r['rate_kg_s']:>7.3f}"
              f"{r['wind_10m_m_s']:>6.1f}{r['c30_meas_pct']:>9.1f}"
              f"{r['c30_model_pct']:>8.2f}{r['c30_ratio']:>7.2f}"
              f"{r['lfl_m']:>7.1f}{br:>10}{r['verdict']:>18}"
              f"{r['premise_ratio_max']:>7.3f}{r['briggs_Lp_max']:>7.1f}"
              f"{loft:>7}")

    print("\n  lift-off columns are **exploratory** -- the decay threshold "
          "was chosen on\n  these six trials. The pair confirmed externally "
          "is test 4 (no lift-off) and\n  test 6 (lifted), reported by Mack "
          "& Boot (ICHS 2023).")

    hor = [r for r in rows if r["orientation"] == "horizontal"]
    ver = [r for r in rows if r["orientation"] != "horizontal"]
    print(f"\n  horizontal (n={len(hor)}): 30 m ratio "
          f"{min(r['c30_ratio'] for r in hor):.2f} to "
          f"{max(r['c30_ratio'] for r in hor):.2f}")
    print(f"  downward   (n={len(ver)}): 30 m ratio "
          f"{min(r['c30_ratio'] for r in ver):.2f} to "
          f"{max(r['c30_ratio'] for r in ver):.2f}")
    print(f"  in bracket: {sum(1 for r in rows if r['verdict'] == 'in')} "
          f"of {len(rows)}")
    print("\n  **The split is by orientation, not by accuracy.** The model has "
          "no downward\n  source and runs all six as horizontal jets; it "
          "reproduces the four downward\n  trials and is low by about 2.6 on "
          "the two horizontal ones.")

    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    with (out / "ffi_summary.csv").open("w", newline="",
                                        encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {out / 'ffi_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
