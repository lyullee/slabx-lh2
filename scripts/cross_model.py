"""
The same trials other models were validated on, run here.

    python scripts/cross_model.py

Writes `paper_results/cross_model.csv`.

Why this and not a table of published numbers
---------------------------------------------
Document 36 concluded that a performance table across models cannot be built
from the literature: the reported endpoints differ, the validation release
rates differ by two orders of magnitude, and each dataset is missing a
different input. That conclusion stands for the literature as a whole.

**It does not stand for FFI tests 4 and 6.** Mack & Boot validated EFFECTS on
exactly those two trials (ICHS 2023), against exactly the same measurement —
the maximum concentration on the 30, 50 and 100 m arcs, taken over sensors at
0.1, 1.0 and 1.8 m. So the comparison can be made properly: run the same two
trials here, against the same measurements, and report the same statistics.

What can and cannot be concluded
--------------------------------
**Their numbers are in scatter plots, not tables.** This script therefore does
not compare model against model. It puts this model on the measurements they
used, and reports what they said about their own result in words, which is
first-hand and unambiguous:

    Test 4  "No plume lift off for all wind speeds and turbulence levels"
            "Maximum values are underpredicted (integral model/CFD-RANS > LES)"
    Test 6  "Sensor at 100m does not detect concentrations: lifted plume"
            "Maximum values close to release are underpredicted"

Those three statements are checkable against what this model does, and they
are what the output below is compared with.

**The convention matters and is theirs.** "Maximum concentration at an arc"
means the largest of the three sensor heights, and the largest reading in
time. Both models take the same thing.

A caution
---------
This work decides on the **LFL distance**, not on concentration, because the
FFI humidity was never reported and the concentration statistics move with
what is assumed for it while the distance does not. The statistics here are
computed at RH 75 % and are reported for comparison with the literature, not
as a basis for any claim.
"""

from __future__ import annotations

import argparse
import collections
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
from slabx_lh2.plume_width import plume_width_coupling           # noqa: E402
from slabx_lh2.trials import FFI                                 # noqa: E402
from slabx_lh2.trials import observations as obs_mod             # noqa: E402
from slabx_lh2.water_ice import with_sublimation                 # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
H2 = Substance(name="H2", mw=0.002016, cp_vapour=14300., cp_liquid=9800.,
               dh_vap=445000., T_boil=20.3, rho_liquid=70.8)
ARCS = (30.0, 50.0, 100.0)
HEIGHTS = (0.1, 1.0, 1.8)
#: The two trials EFFECTS was validated on, and what its authors reported.
PUBLISHED = {
    4: ("no lift-off at any wind speed or turbulence level; maximum values "
        "under-predicted", "grounded"),
    6: ("the 100 m sensor does not detect: lifted plume; maximum values "
        "close to release under-predicted", "lifted"),
}


def measured_arc_maxima(trial: int) -> dict[float, float]:
    """Largest reading on each arc, over the three sensor heights."""
    path = obs_mod.data_dir() / "lh2_ffi_sensors.csv"
    if not path.exists():
        raise obs_mod.ObservationsUnavailable("ffi_arcs")
    best: dict[float, float] = collections.defaultdict(float)
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("kind") != "concentration" or int(r["test"]) != trial:
                continue
            best[float(r["R_m"])] = max(best[float(r["R_m"])],
                                        float(r["max"]))
    return dict(best)


def predicted(trial: int, humidity_pct: float = 75.0):
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
    per_height = {}
    for z in HEIGHTS:
        f = concentration_field(traj, atm, z=z,
                                t_avg=t.averaging_window_s,
                                t_release=t.duration_s)
        per_height[z] = {R: float(np.interp(R, f.x,
                                            np.asarray(f.peak))) * 100.0
                         for R in ARCS}
    arc_max = {R: max(per_height[z][R] for z in HEIGHTS) for R in ARCS}
    peak_height = {R: max(HEIGHTS, key=lambda z: per_height[z][R])
                   for R in ARCS}
    return (traj, atm, arc_max, per_height, peak_height,
            applicability(traj), float(briggs_liftoff(traj, atm).max()))


def statistics(pairs):
    """MG, ln VG, FAC2, MRB -- the set these papers report."""
    p = [(o, m) for o, m in pairs if o > 0.01 and m > 0.01]
    if not p:
        return None
    lo = [math.log(o) for o, _ in p]
    lm = [math.log(m) for _, m in p]
    mg = math.exp(sum(lo) / len(p) - sum(lm) / len(p))
    ln_vg = sum((a - b) ** 2 for a, b in zip(lo, lm)) / len(p)
    fac2 = sum(1 for o, m in p if 0.5 <= m / o <= 2.0) / len(p)
    mrb = 2 * sum((o - m) / (o + m) for o, m in p) / len(p)
    return {"n": len(p), "MG": mg, "ln_VG": ln_vg, "FAC2": fac2, "MRB": mrb}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="paper_results")
    ap.add_argument("--humidity", type=float, default=75.0,
                    help="FFI did not report it; this is an assumption")
    args = ap.parse_args()

    try:
        {t: measured_arc_maxima(t) for t in PUBLISHED}
    except obs_mod.ObservationsUnavailable as exc:
        print(exc)
        print("\nThe model output below does not need them; the comparison "
              "does.")
        return 0

    rows, all_pairs = [], []
    print("FFI tests 4 and 6 -- the trials EFFECTS was validated on")
    print(f"assumed humidity {args.humidity:.0f} % (never reported)\n")

    for trial, (said, expected) in sorted(PUBLISHED.items()):
        t = FFI[trial]
        meas = measured_arc_maxima(trial)
        (_, _, arc_max, per_h, peak_h, app, lp) = predicted(trial,
                                                            args.humidity)
        lifts = lp > 20.0
        print(f"Test {trial}   u = {t.wind_m_s} m/s, q = {t.rate_kg_s} kg/s")
        print(f"  published : {said}")
        print(f"  here      : {app['status']}, w_c/u = "
              f"{app['premise_ratio']:.3f}, Briggs L_p = {lp:.1f} "
              f"({'lifts' if lifts else 'grounded'})"
              f"   {'AGREES' if (expected == 'lifted') == lifts else 'DIFFERS'}")
        print(f"{'arc':>7}{'measured':>10}{'model':>9}{'ratio':>8}"
              f"{'peak at':>9}")
        pairs = []
        for R in ARCS:
            o, m = meas[R], arc_max[R]
            pairs.append((o, m))
            all_pairs.append((o, m))
            print(f"{R:>7.0f}{o:>10.2f}{m:>9.2f}{m / o:>8.2f}"
                  f"{peak_h[R]:>8.1f}m")
            rows.append({
                "trial": trial, "wind_m_s": t.wind_m_s,
                "rate_kg_s": t.rate_kg_s, "arc_m": R,
                "measured_max_pct": o, "model_max_pct": m, "ratio": m / o,
                "model_peak_height_m": peak_h[R],
                **{f"model_at_{z}m_pct": per_h[z][R] for z in HEIGHTS},
                "premise_ratio_max": app["premise_ratio"],
                "briggs_Lp_max": lp,
                "applicability_status": app["status"],
                "assumed_humidity_pct": args.humidity,
            })
        s = statistics(pairs)
        print(f"  MG {s['MG']:.2f}   ln VG {s['ln_VG']:.2f}   "
              f"FAC2 {s['FAC2']:.2f}   MRB {s['MRB']:+.2f}\n")

    s = statistics(all_pairs)
    print(f"both trials, n = {s['n']}:  MG {s['MG']:.2f}   "
          f"ln VG {s['ln_VG']:.2f}   FAC2 {s['FAC2']:.2f}   "
          f"MRB {s['MRB']:+.2f}")
    print("  MG above 1 is under-prediction. For context, ADREA-HF report "
          "MG 0.84\n  on HSL test 5 with humidity and 0.22 without -- "
          "over-prediction, and a\n  different experiment.")

    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    with (out / "cross_model.csv").open("w", newline="",
                                        encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {out / 'cross_model.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
