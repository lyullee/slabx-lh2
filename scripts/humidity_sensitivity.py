"""
Which conclusions survive the humidity that the public FFI report omits?

    python scripts/humidity_sensitivity.py

Writes `paper_results/humidity_sensitivity.{csv,json}`.

The gap
-------
The accessible public FFI report does not tabulate relative humidity. Every
FFI run in this work therefore assumes one. This script does not infer the
unreported value or select the value that fits best.

What is being asked
-------------------
**Not** which humidity makes the numbers look best. The question is whether
the two things the paper concludes hold across the whole plausible range:

    horizontal bias         both horizontal trials remain under-predicted
    strict separation       every horizontal ratio below every downward ratio
    the bracket count       five of six, and which one fails

The first can remain true while strict group separation fails; the output
records them separately.

Everything else is held fixed: the same code, the same trial conditions, the
same modules, the same `slabx`.
"""

from __future__ import annotations

import argparse
import csv
import json
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

from slabx_lh2.diagnostics import applicability                  # noqa: E402
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
RH_GRID = (0.0, 25.0, 50.0, 75.0, 90.0, 100.0)
BASELINE_RH = 75.0


def one(trial: int, rh: float) -> dict:
    t = FFI[trial]
    atm = Atmosphere(u_ref=t.wind_m_s, z_ref=10.0,
                     T=t.temperature_C + 273.15, rh=rh, z0=0.01,
                     stability="D")
    src = HorizontalJet(substance=H2, rate=t.rate_kg_s, area=t.area_m2,
                        duration=t.duration_s,
                        liquid_fraction=t.liquid_fraction,
                        height=t.release_height_m, T_source=20.37)
    with plume_width_coupling():
        traj, _ = run_dispersion(src, atm,
                                 CoolPropThermo(H2, fluid="Hydrogen"),
                                 with_sublimation(coolprop_water()),
                                 x_max=300.0, n_puff_steps=40)
    c30 = 0.0
    for z in HEIGHTS:
        f = concentration_field(traj, atm, z=z, t_avg=t.averaging_window_s,
                                t_release=t.duration_s)
        c30 = max(c30, float(np.interp(30.0, f.x,
                                       np.asarray(f.peak))) * 100)
    d = flammable_distance(traj, atm, t_avg=t.averaging_window_s,
                           t_release=t.duration_s, safety_factor=1.0)
    meas = OB.arc_maxima(trial)
    lo, hi = brackets_from_arcs(ARCS, meas)
    app = applicability(traj)
    return {"trial": trial, "orientation": t.orientation, "rh_pct": rh,
            "rate_kg_s": t.rate_kg_s, "wind_10m_m_s": t.wind_m_s,
            "c30_meas_pct": meas[0], "c30_model_pct": round(c30, 3),
            "c30_ratio": round(c30 / meas[0], 4),
            "lfl_raw_m": round(d["raw"], 3),
            "bracket_lower_m": lo,
            "bracket_upper_m": "" if math.isinf(hi) else hi,
            "verdict": verdict(d["raw"], (lo, hi)),
            "in_bracket": int(verdict(d["raw"], (lo, hi)) == "in"),
            "premise_ratio_max": round(app["premise_ratio"], 4),
            "applicability": app["status"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="paper_results")
    args = ap.parse_args()
    try:
        {t: OB.arc_maxima(t) for t in FFI}
    except OB.ObservationsUnavailable as exc:
        print(exc)
        return 0

    rows = [one(t, rh) for rh in RH_GRID for t in sorted(FFI)]

    print(f"FFI, relative humidity {RH_GRID[0]:.0f} to {RH_GRID[-1]:.0f} %"
          f"   (baseline {BASELINE_RH:.0f} %, never reported)\n")

    print("30 m concentration ratio, model / measured")
    print(f"{'t':>3}{'dir':>6}" + "".join(f"{r:>8.0f}" for r in RH_GRID)
          + f"{'span':>8}")
    for t in sorted(FFI):
        v = [r["c30_ratio"] for r in rows if r["trial"] == t]
        d = "hori" if FFI[t].orientation == "horizontal" else "vert"
        print(f"{t:>3}{d:>6}" + "".join(f"{x:>8.2f}" for x in v)
              + f"{max(v) - min(v):>8.2f}")

    print("\nLFL distance [m], and the bracket verdict")
    print(f"{'t':>3}" + "".join(f"{r:>9.0f}" for r in RH_GRID)
          + f"{'span %':>9}{'verdicts':>28}")
    for t in sorted(FFI):
        sel = [r for r in rows if r["trial"] == t]
        v = [r["lfl_raw_m"] for r in sel]
        vs = {r["verdict"] for r in sel}
        span = (max(v) - min(v)) / float(np.mean(v)) * 100
        print(f"{t:>3}" + "".join(f"{x:>9.2f}" for x in v)
              + f"{span:>9.2f}{'/'.join(sorted(vs)):>28}")

    print(f"\n{'RH':>6}{'in bracket':>13}{'hori range':>16}"
          f"{'vert range':>18}{'status changes':>16}")
    summary = {}
    for rh in RH_GRID:
        sel = [r for r in rows if r["rh_pct"] == rh]
        n_in = sum(r["in_bracket"] for r in sel)
        hor = [r["c30_ratio"] for r in sel
               if r["orientation"] == "horizontal"]
        ver = [r["c30_ratio"] for r in sel
               if r["orientation"] != "horizontal"]
        st = {r["applicability"] for r in sel}
        summary[str(rh)] = {
            "in_bracket": n_in,
            "horizontal_min": min(hor), "horizontal_max": max(hor),
            "downward_min": min(ver), "downward_max": max(ver),
            "separated": max(hor) < min(ver),
            "statuses": sorted(st)}
        print(f"{rh:>6.0f}{n_in:>10} / 6"
              f"{f'{min(hor):.2f} - {max(hor):.2f}':>16}"
              f"{f'{min(ver):.2f} - {max(ver):.2f}':>18}"
              f"{'/'.join(sorted(st)):>16}")

    sep = all(s["separated"] for s in summary.values())
    counts = {s["in_bracket"] for s in summary.values()}
    horizontal_low = all(
        r["c30_ratio"] < 1.0 for r in rows
        if r["orientation"] == "horizontal")
    print(f"\n  both horizontal trials under-predict at every humidity: "
          f"**{horizontal_low}**")
    print(f"  strict orientation groups separate at every humidity: "
          f"**{sep}**")
    print(f"  bracket count across the range: "
          f"**{sorted(counts)}**")
    fails = {r["trial"] for r in rows if not r["in_bracket"]}
    print(f"  trials that ever fall outside: **{sorted(fails)}**")

    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    with (out / "humidity_sensitivity.csv").open(
            "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (out / "humidity_sensitivity.json").write_text(json.dumps(
        {"rh_grid_pct": list(RH_GRID), "baseline_rh_pct": BASELINE_RH,
         "note": "The accessible public FFI report does not tabulate "
                 "relative humidity. This sweep asks which conclusions "
                 "survive the whole range; it does not infer the actual "
                 "humidity or choose the value that fits best.",
         "horizontal_underprediction_at_every_rh": horizontal_low,
         "orientation_separated_at_every_rh": sep,
         "bracket_counts": sorted(counts),
         "trials_ever_outside": sorted(fails),
         "by_rh": summary, "rows": rows}, indent=2), encoding="utf-8")
    print(f"\nwrote {out / 'humidity_sensitivity.csv'} and .json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
