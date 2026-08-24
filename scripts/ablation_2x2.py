"""
Which of the two changes did what: a 2x2 ablation.

    python scripts/ablation_2x2.py --out paper_results

Writes `ablation_2x2.csv` and `negative_controls.csv`.

The question
------------
Every FFI result in this work is produced with **both** the water sublimation
correction and the plume-width coupling active. The coupling only partly
closed the rise on the NASA trials, so without separating the two there is no
basis for saying which of them, if either, is responsible for the FFI outcome.

    W0C0   triple-point clamp, coupling off      = stock slabx
    W1C0   IAPWS sublimation, coupling off
    W0C1   triple-point clamp, coupling on
    W1C1   IAPWS sublimation, coupling on        = what this work reports

Read it this way
----------------
**Do not adopt on the FFI hit count.** The coupling is gated on `is_lofted`,
and none of the FFI trials lofts, so W0C0 = W0C1 and W1C0 = W1C1 there by
construction -- an identical result is the gate working, not the module doing
nothing useful. What the FFI columns can show is the water correction alone.

The NASA columns are where the coupling acts, and the negative controls are
where either of them could do damage. All three go in the paper together.

**Nothing is retuned after seeing this.**
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
from slabx.core.source import EvaporatingPool, HorizontalJet     # noqa: E402
from slabx.post.concentration import concentration_field         # noqa: E402
from slabx.submodels.atmosphere import Atmosphere                # noqa: E402
from slabx.thermo.base import LegacyThermo, Substance, water_backend  # noqa: E402,E501
from slabx.thermo.coolprop import CoolPropThermo, coolprop_water  # noqa: E402

from slabx_lh2.diagnostics import applicability, rise_scaling    # noqa: E402
from slabx_lh2.lfl import (brackets_from_arcs, flammable_distance,  # noqa: E402,E501
                           verdict)
from slabx_lh2.plume_width import plume_width_coupling           # noqa: E402
from slabx_lh2.water_ice import with_sublimation                 # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
H2 = Substance(name="H2", mw=0.002016, cp_vapour=14300., cp_liquid=9800.,
               dh_vap=445000., T_boil=20.3, rho_liquid=70.8)
LNG = Substance(name="LNG", mw=0.016043, cp_vapour=2238., cp_liquid=3348.5,
                dh_vap=509900., T_boil=111.7, rho_liquid=424.1)
SO2 = Substance(name="SO2", mw=0.064066, cp_vapour=622., cp_liquid=1360.,
                dh_vap=389000., T_boil=263.1, rho_liquid=1460.)
A_FFI = math.pi * 0.0254 ** 2 / 4
ARCS = (30., 50., 100.)

from slabx_lh2.trials import FFI as _TRIALS                     # noqa: E402
from slabx_lh2.trials import observations as _obs                # noqa: E402


def _ffi_table():
    out = {}
    for k, t in _TRIALS.items():
        try:
            arcs = _obs.arc_maxima(k)
        except _obs.ObservationsUnavailable:
            arcs = None
        out[k] = (t.rate_kg_s, t.liquid_fraction, t.wind_m_s,
                  t.temperature_C, t.duration_s, t.averaging_window_s, arcs)
    return out


FFI = _ffi_table()
NASA = {2: (1.6, 40, 24., 49.), 6: (2.2, 35, 15., 29.),
        4: (3.6, 33, 15., 43.), 5: (6.3, 24, 12., 43.)}
#  name, stability, u, z_ref, z0, rate, duration, window, observed LFL
LNG_TRIALS = [("BU03", "C", 5.58, 3., 2e-4, 87.98, 167, 100, 190),
              ("BU07", "D", 8.75, 3., 2e-4, 99.46, 174, 140, 264),
              ("BU08", "E", 1.94, 3., 2e-4, 116.93, 107, 80, 455),
              ("BU09", "D", 5.94, 3., 2e-4, 135.98, 79, 50, 406),
              ("CO3", "C", 6.77, 3., 2e-4, 100.70, 65, 50, 206),
              ("CO5", "C", 10.47, 3., 2e-4, 129.00, 98, 90, 245),
              ("CO6", "D", 5.04, 3., 2e-4, 123.00, 82, 70, 219),
              ("MS27", "D", 5.50, 10., 3e-4, 23.20, 160, 160, 177),
              ("MS34", "D", 8.60, 10., 3e-4, 21.50, 95, 95, 167),
              ("MS35", "D", 9.80, 10., 3e-4, 27.10, 135, 135, 184)]


def _traj(src, atm, emission, water, coupling, x_max=300.):
    with plume_width_coupling(coupling):
        return run_dispersion(src, atm, emission, water, x_max=x_max,
                              n_puff_steps=40)[0]


def _shape(traj):
    z = np.asarray(traj.z_c, float)
    return (float(z.max()), float(np.asarray(traj.h, float).max()),
            float(np.asarray(traj.b_half, float).max()))


def run_ffi(trial, ice, coupling):
    q, liq, u, Tc, dur, win, obs = FFI[trial]
    atm = Atmosphere(u_ref=u, z_ref=10., T=Tc + 273.15, rh=75., z0=0.01,
                     stability="D")
    src = HorizontalJet(substance=H2, rate=q, area=A_FFI, duration=float(dur),
                        liquid_fraction=liq, height=0.5, T_source=20.37)
    water = with_sublimation(coolprop_water()) if ice else coolprop_water()
    traj = _traj(src, atm, CoolPropThermo(H2, fluid="Hydrogen"), water,
                 coupling)
    d = flammable_distance(traj, atm, t_avg=win, t_release=float(dur),
                           safety_factor=1.0)
    lo, hi = brackets_from_arcs(ARCS, obs)
    app = applicability(traj)
    zc, h, b = _shape(traj)
    return dict(lfl_m=d["raw"], observed_lower_m=lo,
                observed_upper_m=(None if math.isinf(hi) else hi),
                bracket_verdict=verdict(d["raw"], (lo, hi)),
                premise_ratio_max=app["premise_ratio"],
                max_centerline_height_m=zc, max_half_depth_m=h * 0.5,
                max_half_width_m=b, rise_exponent_fit="",
                applicability_status=app["status"])


def run_nasa(trial, ice, coupling):
    u, ts, Tc, rh = NASA[trial]
    atm = Atmosphere(u_ref=u, z_ref=10., T=Tc + 273.15, rh=rh, z0=3e-3,
                     stability="D")
    src = EvaporatingPool(substance=H2, rate=5.7 * 70.8 / ts,
                          area=math.pi * 4.55 ** 2, duration=float(ts))
    water = with_sublimation(coolprop_water()) if ice else coolprop_water()
    traj = _traj(src, atm, CoolPropThermo(H2, fluid="Hydrogen"), water,
                 coupling, x_max=400.)
    app = applicability(traj)
    zc, h, b = _shape(traj)
    try:
        n = rise_scaling(traj)["exponent"]
    except ValueError:
        n = ""
    return dict(lfl_m="", observed_lower_m="", observed_upper_m="",
                bracket_verdict="", premise_ratio_max=app["premise_ratio"],
                max_centerline_height_m=zc, max_half_depth_m=h * 0.5,
                max_half_width_m=b, rise_exponent_fit=n,
                applicability_status=app["status"])


def run_lng(spec, ice, coupling):
    name, stab, u, zr, z0, q, dur, tav, obs = spec
    atm = Atmosphere(u_ref=u, z_ref=zr, T=290., rh=50., z0=z0, stability=stab)
    src = EvaporatingPool(substance=LNG, rate=q, area=q / (116.93 / 657.0),
                          duration=float(dur))
    water = with_sublimation(water_backend()) if ice else water_backend()
    traj = _traj(src, atm, LegacyThermo(LNG), water, coupling, x_max=1400.)
    f = concentration_field(traj, atm, z=1.0, t_avg=float(tav),
                            t_release=float(dur))
    return f.distance_to(0.05)


def run_passive(ice, coupling):
    atm = Atmosphere(u_ref=4.6, z_ref=2., T=300., rh=40., z0=6e-3,
                     stability="D")
    src = EvaporatingPool(substance=SO2, rate=0.09, area=1.0, duration=1200.)
    water = with_sublimation(water_backend()) if ice else water_backend()
    traj = _traj(src, atm, LegacyThermo(SO2), water, coupling, x_max=600.)
    return np.asarray(traj.z_c, float).copy()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="paper_results")
    args = ap.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for ice in (False, True):
        for cpl in (False, True):
            tag = f"W{int(ice)}C{int(cpl)}"
            print(f"  {tag}")
            for t in sorted(FFI):
                r = run_ffi(t, ice, cpl)
                rows.append(dict(dataset="FFI", case_id=f"test{t}",
                                 water_correction=int(ice),
                                 width_coupling=int(cpl), warning="", error="",
                                 **r))
            for t in sorted(NASA):
                r = run_nasa(t, ice, cpl)
                rows.append(dict(dataset="NASA", case_id=f"test{t}",
                                 water_correction=int(ice),
                                 width_coupling=int(cpl),
                                 warning="outside the bent-over premise"
                                 if r["applicability_status"] == "OUT_OF_SCOPE"
                                 else "", error="", **r))

    cols = ["dataset", "case_id", "water_correction", "width_coupling",
            "lfl_m", "observed_lower_m", "observed_upper_m",
            "bracket_verdict", "premise_ratio_max", "max_centerline_height_m",
            "max_half_depth_m", "max_half_width_m", "rise_exponent_fit",
            "applicability_status", "warning", "error"]
    with (out / "ablation_2x2.csv").open("w", newline="",
                                         encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    # -- negative controls -------------------------------------------------
    print("  negative controls")
    nc = []
    for spec in LNG_TRIALS:
        base = run_lng(spec, False, False)
        var = run_lng(spec, True, True)
        nc.append(dict(dataset="LNG pool", case_id=spec[0],
                       metric="LFL distance [m]", baseline=base, variant=var,
                       relative_change_pct=abs(var - base) / base * 100,
                       bit_identical=int(var == base),
                       acceptance_limit="< 1 %",
                       pass_=int(abs(var - base) / base * 100 < 1.0)))
    a, b = run_passive(False, False), run_passive(True, True)
    nc.append(dict(dataset="Prairie Grass", case_id="SO2 passive",
                   metric="z_c array", baseline="", variant="",
                   relative_change_pct=0.0 if np.array_equal(a, b)
                   else float(np.abs(a - b).max()),
                   bit_identical=int(np.array_equal(a, b)),
                   acceptance_limit="bit-identical",
                   pass_=int(np.array_equal(a, b))))
    with (out / "negative_controls.csv").open("w", newline="",
                                              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["dataset", "case_id", "metric",
                                           "baseline", "variant",
                                           "relative_change_pct",
                                           "bit_identical",
                                           "acceptance_limit", "pass_"])
        w.writeheader()
        w.writerows(nc)

    # -- read it back ------------------------------------------------------
    print(f"\nFFI, distance to the flammable limit [m] and bracket verdict")
    print(f"{'trial':>6}{'W0C0':>10}{'W1C0':>10}{'W0C1':>10}{'W1C1':>10}"
          f"{'observed':>14}")
    for t in sorted(FFI):
        cells = []
        for ice, cpl in ((0, 0), (1, 0), (0, 1), (1, 1)):
            r = next(x for x in rows if x["dataset"] == "FFI"
                     and x["case_id"] == f"test{t}"
                     and x["water_correction"] == ice
                     and x["width_coupling"] == cpl)
            cells.append(r["lfl_m"])
        lo = rows[0] and next(x for x in rows if x["case_id"] == f"test{t}")
        span = (f"{lo['observed_lower_m']:.0f} - "
                f"{lo['observed_upper_m']:.0f}" if lo["observed_upper_m"]
                else f"> {lo['observed_lower_m']:.0f}")
        print(f"{t:>6}" + "".join(f"{c:>10.2f}" for c in cells)
              + f"{span:>14}")

    print(f"\nNASA, fitted rise exponent  (Briggs 0.667)")
    print(f"{'trial':>6}{'W0C0':>10}{'W1C0':>10}{'W0C1':>10}{'W1C1':>10}"
          f"{'w_c/u':>9}")
    for t in sorted(NASA):
        cells = []
        for ice, cpl in ((0, 0), (1, 0), (0, 1), (1, 1)):
            r = next(x for x in rows if x["dataset"] == "NASA"
                     and x["case_id"] == f"test{t}"
                     and x["water_correction"] == ice
                     and x["width_coupling"] == cpl)
            cells.append(r["rise_exponent_fit"])
            last = r
        print(f"{t:>6}" + "".join(
            f"{c:>10.3f}" if isinstance(c, float) else f"{'-':>10}"
            for c in cells) + f"{last['premise_ratio_max']:>9.2f}")

    worst = max(x["relative_change_pct"] for x in nc
                if x["dataset"] == "LNG pool")
    print(f"\nnegative controls: LNG pool worst change {worst:.3f} %, "
          f"passive bit-identical "
          f"{bool(nc[-1]['bit_identical'])}")
    print(f"wrote {out/'ablation_2x2.csv'} and {out/'negative_controls.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
