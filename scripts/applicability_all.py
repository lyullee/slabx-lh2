"""
Screening against diagnosis, on every case this work can reproduce.

    python scripts/applicability_all.py --out paper_results

Writes `applicability_all_cases.csv` and prints the confusion matrices.

Two quantities, and they are not the same
-----------------------------------------
    prescreen   `u_crit = a q^b`, answerable from the release rate and the
                wind alone, **before** anything is integrated. Fitted to a
                pool source over 0.1 to 30 kg/s.

    diagnosis   `Pi = max(w_c/u)` read off the trajectory the model actually
                produced. This is the one with authority.

The operational point of the paper is that **the screen does not decide**. It
exists so that a monitoring loop can skip an integration it is going to
refuse, and it is deliberately conservative: it knows nothing about the source
geometry, and a momentum jet resists lofting in a way a pool does not.

So a disagreement is expected, and its direction matters. A `false_flag` --
screen says outside, model says inside -- costs an unnecessary integration. A
`miss` -- screen says inside, model says outside -- would be the dangerous
one, because a caller that trusted the screen alone would use a number the
model does not stand behind.

**These are not two classifiers being compared for accuracy.** One is a
property of the inputs and the other is a property of the solution; there is
no ground truth here, and reporting a single accuracy figure would imply one.
"""

from __future__ import annotations

import argparse
import csv
import math
import warnings
from collections import Counter
from pathlib import Path

warnings.simplefilter("ignore")

from slabx.core.plume import run_dispersion                      # noqa: E402
from slabx.core.source import EvaporatingPool, HorizontalJet     # noqa: E402
from slabx.submodels.atmosphere import Atmosphere                # noqa: E402
from slabx.thermo.base import Substance                          # noqa: E402
from slabx.thermo.coolprop import CoolPropThermo, coolprop_water  # noqa: E402

from slabx_lh2.diagnostics import (CRITICAL_WIND_FIT,            # noqa: E402
                                   CRITICAL_WIND_RANGE_KGS,
                                   applicability, critical_wind)
from slabx_lh2.plume_width import plume_width_coupling           # noqa: E402
from slabx_lh2.water_ice import with_sublimation                 # noqa: E402

import CoolProp.CoolProp as CP                                   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
H2 = Substance(name="H2", mw=0.002016, cp_vapour=14300., cp_liquid=9800.,
               dh_vap=445000., T_boil=20.3, rho_liquid=70.8)
A_FFI = math.pi * 0.0254 ** 2 / 4

FFI = {1: (0.225, 0.888, 3.2, 1.0, 780), 3: (0.730, 0.559, 5.8, 2.9, 900),
       4: (0.828, 0.559, 6.7, 3.3, 360), 5: (0.715, 0.559, 5.2, 3.7, 240),
       6: (0.832, 0.559, 2.7, 3.8, 180), 7: (0.162, 0.949, 6.5, 3.2, 480)}
NASA = {2: (1.6, 40, 24., 49.), 6: (2.2, 35, 15., 29.),
        4: (3.6, 33, 15., 43.), 5: (6.3, 24, 12., 43.)}
#  Zhang et al. 2024: volume m3, duration s, T K, RH %, u m/s
ZHANG = {5: (3.0, 4, 291.73, 28.83, 0.13), 6: (2.5, 40, 282.54, 39.76, 0.30),
         7: (2.5, 30, 277.76, 27.63, 0.04), 8: (2.5, 48, 279.17, 29.21, 0.05),
         9: (1.5, 25, 283.06, 27.46, 0.61), 10: (3.0, 4, 282.05, 46.11, 0.11),
         11: (3.0, 5, 307.82, 79.55, 0.01),
         12: (0.5, 20, 307.67, 67.13, 0.15)}
E35_TESTS = {"3.5.1": ("h", 0.5, 25.4, 1), "3.5.2": ("h", 0.5, 12, 1),
             "3.5.4": ("h", 1.5, 25.4, 1), "3.5.5": ("h", 1.5, 12, 1),
             "3.5.7": ("u", 0.5, 12, 1), "3.5.8": ("d", 0.5, 12, 1),
             "3.5.10": ("h", 0.5, 25.4, 5), "3.5.11": ("h", 0.5, 12, 5),
             "3.5.12": ("h", 0.5, 6, 5), "3.5.13": ("h", 1.5, 25.4, 5),
             "3.5.14": ("h", 1.5, 12, 5), "3.5.15": ("h", 1.5, 6, 5),
             "3.5.16": ("u", 0.5, 12, 5), "3.5.17": ("d", 0.5, 12, 5)}
E35_TRIAL = {3: "3.5.1", 4: "3.5.2", 6: "3.5.7", 7: "3.5.8", 8: "3.5.8",
             10: "3.5.10", 11: "3.5.11", 12: "3.5.12", 13: "3.5.17",
             14: "3.5.16", 16: "3.5.4", 17: "3.5.5", 19: "3.5.4",
             20: "3.5.5", 22: "3.5.13", 23: "3.5.14", 24: "3.5.15"}
E35_FLOW = {(25.4, 1): 0.1395, (12, 1): 0.1055, (25.4, 5): 0.298,
            (12, 5): 0.265, (6, 5): 0.095}


def _flash(bar):
    h0 = CP.PropsSI("H", "P", bar * 1e5 + 101325., "Q", 0, "Hydrogen")
    return float(CP.PropsSI("Q", "P", 101325., "H", h0, "Hydrogen"))


def _judge(src, atm, x_max=300.):
    with plume_width_coupling():
        traj, _ = run_dispersion(src, atm, CoolPropThermo(H2, fluid="Hydrogen"),
                                 with_sublimation(coolprop_water()),
                                 x_max=x_max, n_puff_steps=40)
    return applicability(traj)


def _row(dataset, case, kind, orient, q, u, zref, stab, z0, app):
    screen_u = critical_wind(q, stab)
    screen_in = u >= screen_u
    direct_in = app["status"] != "OUT_OF_SCOPE"
    if screen_in and direct_in:
        cmp = "agree_inside"
    elif not screen_in and not direct_in:
        cmp = "agree_outside"
    elif not screen_in and direct_in:
        cmp = "false_flag"
    else:
        cmp = "miss"
    return {"dataset": dataset, "case_id": case, "source_type": kind,
            "orientation": orient, "rate_kg_s": q, "wind_ref_m_s": u,
            "wind_ref_height_m": zref, "stability": stab, "z0_m": z0,
            "prescreen_ucrit_m_s": screen_u,
            "prescreen_status": "inside" if screen_in else "outside",
            "premise_ratio_max": app["premise_ratio"],
            "rise_angle_deg": app["angle_deg"],
            "direct_status": app["status"],
            "screen_vs_direct": cmp, "error": ""}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="paper_results")
    args = ap.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    rows = []

    print("  FFI")
    for t, (q, liq, u, Tc, dur) in sorted(FFI.items()):
        atm = Atmosphere(u_ref=u, z_ref=10., T=Tc + 273.15, rh=75., z0=0.01,
                         stability="D")
        src = HorizontalJet(substance=H2, rate=q, area=A_FFI,
                            duration=float(dur), liquid_fraction=liq,
                            height=0.5, T_source=20.37)
        rows.append(_row("FFI", f"test{t}", "jet", "horizontal", q, u, 10.,
                         "D", 0.01, _judge(src, atm)))

    print("  PRESLHY E3.5")
    # conditions come from `slabx_lh2.trials`, which ships with the package;
    # the extracted CSV is a measurement file and is not distributed
    from slabx_lh2.trials import E35
    for t, tr in sorted(E35.items()):
        ori = {"horizontal": "h", "vertical up": "u",
               "vertical down": "d"}[tr.orientation]
        hgt, d = tr.release_height_m, tr.nozzle_mm
        bar = 5 if "5 barg" in tr.note else 1
        q, u = tr.rate_kg_s, tr.wind_m_s
        atm = Atmosphere(u_ref=u, z_ref=tr.wind_ref_height_m,
                         T=tr.temperature_C + 273.15, rh=tr.humidity_pct,
                         z0=tr.roughness_m, stability=tr.stability)
        if ori == "d":
            src = EvaporatingPool(substance=H2, rate=q, duration=120.,
                                  area=math.pi * tr.pool_radius_m ** 2)
            kind, orient = "pool", "vertical down"
        else:
            src = HorizontalJet(substance=H2, rate=q, duration=120.,
                                area=math.pi * (d / 1000.) ** 2 / 4,
                                liquid_fraction=1 - _flash(bar), height=hgt,
                                T_source=20.37)
            kind = "jet"
            orient = "horizontal" if ori == "h" else "vertical up"
        rows.append(_row("PRESLHY E3.5", f"trial{t}", kind, orient, q, u,
                         tr.wind_ref_height_m, tr.stability, tr.roughness_m,
                         _judge(src, atm, x_max=40.)))

    print("  NASA")
    for t, (u, ts, Tc, rh) in sorted(NASA.items()):
        q = 5.7 * 70.8 / ts
        atm = Atmosphere(u_ref=u, z_ref=10., T=Tc + 273.15, rh=rh, z0=3e-3,
                         stability="D")
        src = EvaporatingPool(substance=H2, rate=q,
                              area=math.pi * 4.55 ** 2, duration=float(ts))
        rows.append(_row("NASA", f"test{t}", "pool", "ground spill", q, u,
                         10., "D", 3e-3, _judge(src, atm, x_max=400.)))

    print("  Zhang et al. 2024")
    for t, (vol, dur, T, rh, u) in sorted(ZHANG.items()):
        q = vol * 70.8 / dur
        atm = Atmosphere(u_ref=max(u, 0.05), z_ref=10., T=T, rh=rh, z0=0.01,
                         stability="D")
        src = EvaporatingPool(substance=H2, rate=q, area=36.,
                              duration=float(dur))
        rows.append(_row("Zhang 2024", f"test{t}", "pool", "ground spill", q,
                         u, 10., "D", 0.01, _judge(src, atm, x_max=400.)))

    with (out / "applicability_all_cases.csv").open(
            "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # ---- read it back ----------------------------------------------------
    def matrix(sel, label):
        c = Counter(r["screen_vs_direct"] for r in sel)
        n = len(sel)
        print(f"\n{label}  (n = {n})")
        print(f"{'':>22}{'model inside':>15}{'model outside':>15}")
        print(f"{'screen inside':>22}{c['agree_inside']:>15}"
              f"{c['miss']:>15}")
        print(f"{'screen outside':>22}{c['false_flag']:>15}"
              f"{c['agree_outside']:>15}")
        if c["miss"]:
            print(f"  ** {c['miss']} miss: the screen would have let a case "
                  f"through that the model refuses")
        return c

    total = matrix(rows, "all cases")
    for kind in ("jet", "pool"):
        matrix([r for r in rows if r["source_type"] == kind],
               f"source type: {kind}")

    ff = [r for r in rows if r["screen_vs_direct"] == "false_flag"]
    print(f"\nfalse flags: {len(ff)}, of which "
          f"{sum(1 for r in ff if r['source_type'] == 'jet')} are jets")
    for r in ff:
        print(f"  {r['dataset']:>14} {r['case_id']:>9}  "
              f"{r['source_type']:>5}  q={r['rate_kg_s']:.3f}  "
              f"u={r['wind_ref_m_s']:.2f}  u_crit="
              f"{r['prescreen_ucrit_m_s']:.2f}  Pi="
              f"{r['premise_ratio_max']:.3f}")

    print(f"\nagreement {total['agree_inside'] + total['agree_outside']} "
          f"of {len(rows)}; **not an accuracy** -- there is no ground truth "
          f"here,\nonly a conservative screen and the model's own state.")

    lo, hi = CRITICAL_WIND_RANGE_KGS
    outside = [r for r in rows if not lo <= r["rate_kg_s"] <= hi]
    print(f"\n{len(outside)} cases lie outside the {lo} to {hi} kg/s range "
          f"the screen was fitted over:")
    for r in outside:
        print(f"  {r['dataset']:>14} {r['case_id']:>9}  "
              f"q={r['rate_kg_s']:.2f} kg/s   (extrapolated)")
    print(f"\ncritical_wind coefficients, u_crit = a q^b")
    for k, (a, b) in CRITICAL_WIND_FIT.items():
        print(f"  {k}: a = {a:.3f}, b = {b:.3f}")
    print(f"wrote {out/'applicability_all_cases.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
