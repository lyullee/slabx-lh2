"""
Audit whether the FFI 30 m arc defines the cross-section used by mass balance.

    python scripts/sensor_audit.py

Writes ``paper_results/sensor_audit.csv`` and ``sensor_provenance.csv``.

The answer is **no** for two independent reasons.

1. The instruments lie on a polar arc of radius 30 m. After rotation into the
   mean-wind frame they do not share one downwind coordinate, so integrating
   bearing as though it were a lateral line at ``x = 30 m`` is not valid.
2. The published table contains window averages and temporal maxima. The
   concentration validation uses the maximum of the temporal maxima, whereas
   a previous sensor audit integrated the window averages. A ratio between
   those two statistics is not a spatial peak-to-bulk conversion.

The vertical structure is also unresolved: instruments stop at 1.8 m while
the modelled cloud is deeper. This script therefore reports coordinates and
coverage only. It deliberately produces no lateral or cross-sectional mean.
"""

from __future__ import annotations

import argparse
import csv
import math
import warnings
from pathlib import Path

import numpy as np

warnings.simplefilter("ignore")

from slabx.core.plume import run_dispersion                       # noqa: E402
from slabx.core.source import HorizontalJet                       # noqa: E402
from slabx.submodels.atmosphere import Atmosphere                 # noqa: E402
from slabx.thermo.base import Substance                           # noqa: E402
from slabx.thermo.coolprop import CoolPropThermo, coolprop_water  # noqa: E402

from slabx_lh2.plume_width import plume_width_coupling            # noqa: E402
from slabx_lh2.trials import FFI                                  # noqa: E402
from slabx_lh2.trials import observations as OB                   # noqa: E402
from slabx_lh2.water_ice import with_sublimation                  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
H2 = Substance(name="H2", mw=0.002016, cp_vapour=14300.,
               cp_liquid=9800., dh_vap=445000., T_boil=20.3,
               rho_liquid=70.8)
ARC = 30.0

#: Every flux figure previously quoted at 30 m on FFI test 6.
PROVENANCE = [
    {"value_kg_s": 264.0, "where": "docs/48, withdrawn",
     "x_m": 30.0, "definition": "R_flux(30)/R_flux(0) x release rate",
     "half_or_total": "neither",
     "note": "R_flux[0] is half the release rate; the wrong base was used"},
    {"value_kg_s": 127.3, "where": "docs/52 first revision, withdrawn",
     "x_m": 30.0, "definition": "R_flux(30) read directly",
     "half_or_total": "half", "note": "R_flux is a half-plume flux"},
    {"value_kg_s": 254.630, "where": "docs/52 current",
     "x_m": 30.0, "definition": "2 x R_flux(30)",
     "half_or_total": "total",
     "note": "model quantity only; no observed flux is identifiable from "
             "the available arc sensors"},
]


def sensor_rows(trial: int, arc: float = ARC) -> list[dict]:
    """Concentration instruments on one polar arc."""
    path = OB.data_dir() / "lh2_ffi_sensors.csv"
    if not path.exists():
        raise OB.ObservationsUnavailable("ffi_arcs")
    out = []
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if (r.get("kind") != "concentration" or int(r["test"]) != trial
                    or float(r["R_m"]) != arc):
                continue
            out.append({"sensor": r["sensor"], "z_m": float(r["z_m"]),
                        "bearing_deg": float(r["bearing_deg"]),
                        "window_average_pct": float(r["average"]),
                        "temporal_max_pct": float(r["max"]),
                        "w0": float(r["window_start_s"]),
                        "w1": float(r["window_end_s"])})
    return out


def wind_metadata(trial: int) -> tuple[float, float]:
    """Mean meteorological wind direction and its reported SD [degrees]."""
    path = OB.data_dir() / "lh2_ffi_conditions.csv"
    if not path.exists():
        raise OB.ObservationsUnavailable("ffi_arcs")
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if int(r["test"]) == trial:
                return float(r["wind_dir_deg"]), float(r["wind_dir_sd_deg"])
    raise ValueError(f"FFI test {trial} is absent from {path}")


def wind_frame(bearing_deg: float, wind_from_deg: float,
               radius_m: float = ARC) -> tuple[float, float, float]:
    """Return downwind bearing and ``(x_downwind, y_crosswind)`` [m]."""
    downwind_deg = (wind_from_deg + 180.0) % 360.0
    delta = math.radians(bearing_deg - downwind_deg)
    return (downwind_deg, radius_m * math.cos(delta),
            radius_m * math.sin(delta))


def model_trajectory(trial: int):
    t = FFI[trial]
    atm = Atmosphere(u_ref=t.wind_m_s, z_ref=10.0,
                     T=t.temperature_C + 273.15, rh=75.0, z0=0.01,
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
    return traj


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="paper_results")
    ap.add_argument("--trials", type=int, nargs="*", default=[4, 6])
    args = ap.parse_args()

    try:
        raw = {t: sensor_rows(t) for t in args.trials}
        winds = {t: wind_metadata(t) for t in args.trials}
    except OB.ObservationsUnavailable as exc:
        print(exc)
        return 0

    output = []
    print("FFI 30 m polar-arc sensor audit\n")
    for trial in args.trials:
        rows = raw[trial]
        wind_from, wind_sd = winds[trial]
        traj = model_trajectory(trial)
        tx = np.asarray(traj.x, float)

        located = []
        for row in rows:
            down, x, y = wind_frame(row["bearing_deg"], wind_from)
            located.append((row, down, x, y))
        unique_x = sorted({round(v[2], 12) for v in located})
        depths = [float(np.interp(x, tx, np.asarray(traj.h, float)))
                  for x in unique_x]
        centres = [float(np.interp(x, tx, np.asarray(traj.z_c, float)))
                   for x in unique_x]
        x_span = max(unique_x) - min(unique_x)
        windows = {(row["w0"], row["w1"]) for row in rows}

        print(f"Test {trial}: wind from {wind_from:.0f} +/- {wind_sd:.0f} deg; "
              f"downwind bearing {located[0][1]:.0f} deg")
        print(f"  arc instruments map to x = {min(unique_x):.2f} to "
              f"{max(unique_x):.2f} m (span {x_span:.2f} m)")
        print(f"  model depth over those x positions = {min(depths):.2f} to "
              f"{max(depths):.2f} m; sensor top = "
              f"{max(row['z_m'] for row in rows):.1f} m")
        print("  no fixed-x lateral mean and no cross-sectional mean\n")

        for row, down, x, y in located:
            output.append({
                "trial": trial, "sensor": row["sensor"],
                "z_m": row["z_m"], "radius_m": ARC,
                "bearing_deg": row["bearing_deg"],
                "wind_from_deg": wind_from, "wind_dir_sd_deg": wind_sd,
                "downwind_bearing_deg": round(down, 3),
                "x_downwind_m": round(x, 4),
                "y_crosswind_m": round(y, 4),
                "window_average_pct": row["window_average_pct"],
                "temporal_max_pct": row["temporal_max_pct"],
                "window_s": f"{row['w0']:.0f}-{row['w1']:.0f}",
                "x_span_across_arc_m": round(x_span, 4),
                "model_depth_min_m": round(min(depths), 3),
                "model_depth_max_m": round(max(depths), 3),
                "model_centreline_min_m": round(min(centres), 3),
                "model_centreline_max_m": round(max(centres), 3),
                "sensor_top_m": max(v[0]["z_m"] for v in located),
                "lateral_mean_identifiable": 0,
                "vertical_mean_identifiable": 0,
                "cross_section_mean_identifiable": 0,
                "common_time_window": int(len(windows) == 1),
                "note": "polar arc; not a common downwind plane",
            })

    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    with (out / "sensor_audit.csv").open("w", newline="",
                                         encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    with (out / "sensor_provenance.csv").open("w", newline="",
                                              encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(PROVENANCE[0]))
        writer.writeheader()
        writer.writerows(PROVENANCE)

    print("Conclusion: the arc data do not identify the lateral or vertical "
          "mean on a fixed-x cross-section. No observed total flux or "
          "measured peak-to-bulk conversion is reported.")
    print(f"wrote {out / 'sensor_audit.csv'} and sensor_provenance.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
