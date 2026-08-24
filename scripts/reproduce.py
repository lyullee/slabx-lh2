"""
Reproduce the headline numbers of docs/24_LH2_SUMMARY.md.

    python scripts/reproduce.py                  all sections, printed
    python scripts/reproduce.py water            one section
    python scripts/reproduce.py --json           also write results/results.json

Everything here is a re-run, not a fit. Nothing is tuned.

Every number that appears in a paper, a report or a slide should come from
`results/results.json`, written by this script, and not be typed from a
document. Four of the corrections in `docs/24_LH2_SUMMARY.md` section 24.10
are transcription or attribution errors; a value that is generated cannot
acquire one. `docs/26_RESULTS_REGISTER.md` maps each key to what it means and
what it may be claimed as.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json as _json
import math
import sys
from pathlib import Path as _Path

import CoolProp.CoolProp as _CP
import numpy as np

from slabx.core.plume import run_dispersion
from slabx.core.source import EvaporatingPool, HorizontalJet
from slabx.post.concentration import concentration_field
from slabx.submodels.atmosphere import Atmosphere
from slabx.thermo.base import LegacyThermo, Substance, water_backend
from slabx.thermo.coolprop import CoolPropThermo, coolprop_water

import slabx as _slabx
from slabx_lh2 import __version__ as _version
from slabx_lh2.diagnostics import briggs_liftoff, critical_wind, premise_summary
from slabx_lh2.lfl import (SAFETY_FACTOR, brackets_from_arcs,
                           flammable_distance, verdict)
from slabx_lh2.plume_width import plume_width_coupling
from slabx_lh2.vertical_drag import vertical_drag
from slabx_lh2.air_condensation import condensation_onset
from slabx_lh2.diagnostics import (CRITICAL_WIND_FIT, CRITICAL_WIND_RANGE_KGS,
                                   rise_scaling)
from slabx_lh2.pool import (CRITICAL_HEAT_FLUX, flux_from_regression,
                            ground_limited_flux, pool_radius, substrate)
from slabx_lh2.water_ice import p_sublimation, with_sublimation

H2 = Substance(name="H2", mw=0.002016, cp_vapour=14300.0, cp_liquid=9800.0,
               dh_vap=445000.0, T_boil=20.3, rho_liquid=70.8)
LNG = Substance(name="LNG", mw=0.016043, cp_vapour=2238.0, cp_liquid=3348.5,
                dh_vap=509900.0, T_boil=111.7, rho_liquid=424.1)
A_FFI = math.pi * 0.0254 ** 2 / 4
ARCS = (30.0, 50.0, 100.0)


def _ffi_table():
    """
    Conditions from `slabx_lh2.trials`, arc maxima from the measurements if
    they are installed.

    The conditions ship with the package; the arc maxima do not. Where they
    are missing the bracket verdict cannot be computed and the entry carries
    `None`, which the caller must handle rather than silently skip.
    """
    from slabx_lh2.trials import FFI as _T
    from slabx_lh2.trials import observations as _obs
    out = {}
    for k, t in _T.items():
        try:
            arcs = _obs.arc_maxima(k)
        except _obs.ObservationsUnavailable:
            arcs = None
        out[k] = (t.rate_kg_s, t.liquid_fraction, t.wind_m_s,
                  t.temperature_C, t.duration_s, t.averaging_window_s, arcs)
    return out


FFI = _ffi_table()
#  name, stability, u, z_ref, z0, rate, duration, averaging window, observed
LNG_TRIALS = [("BU03", "C", 5.58, 3.0, 2e-4, 87.98, 167, 100, 190),
              ("BU07", "D", 8.75, 3.0, 2e-4, 99.46, 174, 140, 264),
              ("BU08", "E", 1.94, 3.0, 2e-4, 116.93, 107, 80, 455),
              ("BU09", "D", 5.94, 3.0, 2e-4, 135.98, 79, 50, 406),
              ("CO3", "C", 6.77, 3.0, 2e-4, 100.70, 65, 50, 206),
              ("CO5", "C", 10.47, 3.0, 2e-4, 129.00, 98, 90, 245),
              ("CO6", "D", 5.04, 3.0, 2e-4, 123.00, 82, 70, 219),
              ("MS27", "D", 5.50, 10.0, 3e-4, 23.20, 160, 160, 177),
              ("MS34", "D", 8.60, 10.0, 3e-4, 21.50, 95, 95, 167),
              ("MS35", "D", 9.80, 10.0, 3e-4, 27.10, 135, 135, 184)]
#  Witcofski & Chirivella (1984) Table 1: wind, spill time, T_C, RH
NASA = {2: (1.6, 40, 24.0, 49.0), 6: (2.2, 35, 15.0, 29.0),
        4: (3.6, 33, 15.0, 43.0), 5: (6.3, 24, 12.0, 43.0)}


def _ffi(trial, rh=75.0, coupling=True):
    q, liq, u, Tc, dur, win, _ = FFI[trial]
    atm = Atmosphere(u_ref=u, z_ref=10.0, T=Tc + 273.15, rh=rh, z0=0.01,
                     stability="D")
    src = HorizontalJet(substance=H2, rate=q, area=A_FFI, duration=float(dur),
                        liquid_fraction=liq, height=0.5, T_source=20.37)
    with plume_width_coupling(coupling):
        traj, _ = run_dispersion(src, atm, CoolPropThermo(H2, fluid="Hydrogen"),
                                 with_sublimation(coolprop_water()),
                                 x_max=300.0, n_puff_steps=40)
    return atm, traj, dur, win


def section_water():
    print("== water saturation below the triple point ==")
    stock = coolprop_water()
    print(f"{'T [K]':>8}{'stock':>13}{'IAPWS':>13}{'stock/IAPWS':>14}")
    for T in (273.16, 260.0, 240.0, 200.0, 150.0):
        a = stock.saturation_ratio(T) * 101325.0
        b = p_sublimation(T)
        print(f"{T:>8.2f}{a:>13.4e}{b:>13.4e}{a / b:>14.1f}")


def section_dense():
    print("\n== negative control: Burro 8, LNG pool ==")
    atm = Atmosphere(u_ref=1.94, z_ref=3.0, T=290.0, rh=50.0, z0=2e-4,
                     stability="E")
    src = dict(rate=116.93, area=116.93 / (116.93 / 657.0), duration=107.0)
    out = {}
    for label, water, cpl in (("stock", water_backend(), False),
                              ("both modules",
                               with_sublimation(water_backend()), True)):
        with plume_width_coupling(cpl):
            traj, _ = run_dispersion(EvaporatingPool(substance=LNG, **src),
                                     atm, LegacyThermo(LNG), water,
                                     x_max=1000.0, n_puff_steps=40)
        f = concentration_field(traj, atm, z=1.0, t_avg=80.0, t_release=107.0)
        out[label] = f.distance_to(0.05)
        print(f"  {label:<14} LFL distance {out[label]:8.2f} m")
    a, b = out["stock"], out["both modules"]
    print(f"  observed 455 m; change {abs(b - a) / a * 100:.2f} %")


def section_pool():
    print("\n== pool equilibrium radius ==")
    cases = [("E3.5 trial 7", 0.1055, 1.0, 0.70),
             ("E3.5 trial 13", 0.2650, 5.0, 1.20),
             ("RR986 test 6", 0.0708, 1.0, 0.83),
             ("FFI Test 1", 0.2250, 2.0, 0.75),
             ("FFI Test 7", 0.1620, 0.8, 0.75),
             ("FFI Test 3", 0.7300, 10.0, 0.75)]
    ratios = []
    print(f"{'case':<16}{'x_vap':>8}{'R pred':>9}{'R obs':>8}{'ratio':>8}")
    for label, q, barg, obs in cases:
        r = pool_radius(rate=q, tanker_barg=barg, fluid="Hydrogen",
                        rho_liquid=70.8)
        ratios.append(r["radius"] / obs)
        print(f"{label:<16}{r['vapour_fraction']:>8.3f}{r['radius']:>9.2f}"
              f"{obs:>8.2f}{ratios[-1]:>8.2f}")
    print(f"  median {sorted(ratios)[len(ratios) // 2]:.2f}")


def section_premise():
    print("\n== bent-over premise ==")
    print(f"{'case':<22}{'max w_c/u':>11}{'angle':>8}   verdict")
    for t in (4, 6):
        _, traj, _, _ = _ffi(t)
        s = premise_summary(traj)
        print(f"{'FFI Test ' + str(t):<22}{s['max']:>11.3f}"
              f"{s['angle_deg']:>7.1f}"
              f"   {'outside' if s['violated'] else 'inside'}")
    atm = Atmosphere(u_ref=2.2, z_ref=10.0, T=288.15, rh=29.0, z0=3e-3,
                     stability="D")
    with plume_width_coupling():
        traj, _ = run_dispersion(
            EvaporatingPool(substance=H2, rate=5.7 * 70.8 / 35,
                            area=math.pi * 4.55 ** 2, duration=35.0),
            atm, CoolPropThermo(H2, fluid="Hydrogen"),
            with_sublimation(coolprop_water()), x_max=200.0, n_puff_steps=40)
    s = premise_summary(traj)
    print(f"{'NASA Test 6':<22}{s['max']:>11.3f}{s['angle_deg']:>7.1f}"
          f"   {'outside' if s['violated'] else 'inside'}")
    print(f"\n  critical wind, stability D:")
    for q in (0.3, 1.0, 3.0, 9.5, 30.0):
        print(f"    {q:>5.1f} kg/s -> {critical_wind(q):.1f} m/s")


def section_briggs():
    print("\n== Briggs lift-off parameter, FFI ==")
    print(f"{'trial':>6}{'u10':>6}{'u*':>7}{'max L_p':>10}   measured at 100 m")
    obs = {1: "detects", 3: "detects", 4: "detects", 5: "detects",
           6: "does NOT detect", 7: "detects"}
    for t in sorted(FFI):
        atm, traj, _, _ = _ffi(t)
        lp = float(briggs_liftoff(traj, atm).max())
        print(f"{t:>6}{FFI[t][2]:>6.1f}{atm.u_star:>7.3f}{lp:>10.1f}"
              f"   {obs[t]}")
    print("  threshold 20; it separates this set and does not transfer to "
          "NASA -- see docs/prereg/PREREG_lh2_briggs_liftoff.md")


def section_lfl():
    """
    The model's distance, and the measured bracket where it is installed.

    The distance is a model output and always prints. The bracket is a
    measurement and is not distributed; where it is missing the verdict
    column says so rather than the section failing.
    """
    have = any(v[6] is not None for v in FFI.values())
    print("\n== LFL distance"
          + (" against the measured bracket ==" if have
             else " (measured brackets not installed) =="))
    print(f"{'trial':>6}{'measured':>16}{'model':>9}{'x1.25':>9}   verdict")
    for t in sorted(FFI):
        atm, traj, dur, win = _ffi(t)
        d = flammable_distance(traj, atm, t_avg=win, t_release=float(dur))
        if FFI[t][6] is None:
            print(f"{t:>6}{'not installed':>16}{d['raw']:>9.1f}"
                  f"{d['factored']:>9.1f}   -")
            continue
        lo, hi = brackets_from_arcs(ARCS, FFI[t][6])
        span = f"{lo:.0f} - {hi:.0f} m" if math.isfinite(hi) else f"> {lo:.0f} m"
        print(f"{t:>6}{span:>16}{d['raw']:>9.1f}{d['factored']:>9.1f}"
              f"   {verdict(d['raw'], (lo, hi))}")
    if not have:
        print("   the brackets come from FFI-RAPPORT 20/03101 appendix A; "
              "see data/SOURCES.md")


SECTIONS = {"water": section_water, "dense": section_dense,
            "pool": section_pool, "premise": section_premise,
            "briggs": section_briggs, "lfl": section_lfl}


def collect() -> dict:
    """
    Every reportable number, keyed. See docs/26_RESULTS_REGISTER.md for what
    each key means, its grade, and what it may be claimed as.
    """
    out: dict = {"generated_utc": _dt.datetime.now(_dt.timezone.utc)
                 .strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "slabx_lh2_version": _version,
                 "slabx_version": getattr(_slabx, "__version__", "unknown")}

    stock = coolprop_water()
    out["water_saturation_error"] = {
        f"{T:.2f}": {"stock_Pa": stock.saturation_ratio(T) * 101325.0,
                     "iapws_Pa": p_sublimation(T),
                     "ratio": stock.saturation_ratio(T) * 101325.0
                     / p_sublimation(T)}
        for T in (273.16, 260.0, 240.0, 200.0, 150.0)}

    atm = Atmosphere(u_ref=1.94, z_ref=3.0, T=290.0, rh=50.0, z0=2e-4,
                     stability="E")
    src = dict(rate=116.93, area=116.93 / (116.93 / 657.0), duration=107.0)
    burro = {}
    for label, water, cpl in (("stock", water_backend(), False),
                              ("modules", with_sublimation(water_backend()),
                               True)):
        with plume_width_coupling(cpl):
            traj, _ = run_dispersion(EvaporatingPool(substance=LNG, **src),
                                     atm, LegacyThermo(LNG), water,
                                     x_max=1000.0, n_puff_steps=40)
        f = concentration_field(traj, atm, z=1.0, t_avg=80.0, t_release=107.0)
        burro[label] = f.distance_to(0.05)
    burro["observed_m"] = 455.0
    burro["change_pct"] = abs(burro["modules"] - burro["stock"]) \
        / burro["stock"] * 100.0
    out["negative_control_burro8"] = burro

    radii = {}
    for label, q, barg, obs in (("e35_trial7", 0.1055, 1.0, 0.70),
                                ("e35_trial13", 0.2650, 5.0, 1.20),
                                ("rr986_test6", 0.0708, 1.0, 0.83),
                                ("ffi_test1", 0.2250, 2.0, 0.75),
                                ("ffi_test7", 0.1620, 0.8, 0.75),
                                ("ffi_test3", 0.7300, 10.0, 0.75)):
        r = pool_radius(rate=q, tanker_barg=barg, fluid="Hydrogen",
                        rho_liquid=70.8)
        radii[label] = {"predicted_m": r["radius"], "observed_m": obs,
                        "ratio": r["radius"] / obs,
                        "vapour_fraction": r["vapour_fraction"]}
    vals = sorted(v["ratio"] for v in radii.values())
    radii["median_ratio"] = 0.5 * (vals[len(vals)//2 - 1] + vals[len(vals)//2])
    out["pool_radius"] = radii

    ffi = {}
    for t in sorted(FFI):
        if FFI[t][6] is None:
            # the arc maxima are not installed, so there is nothing to
            # bracket the model against; the model output still stands and is
            # recorded without a verdict
            a, traj, dur, win = _ffi(t)
            s_ = premise_summary(traj)
            d = flammable_distance(traj, a, t_avg=win, t_release=float(dur))
            ffi[str(t)] = {
                "wind_10m_ms": FFI[t][2], "rate_kgs": FFI[t][0],
                "u_star_ms": a.u_star, "premise_ratio_max": s_["max"],
                "premise_violated": s_["violated"],
                "briggs_Lp_max": float(briggs_liftoff(traj, a).max()),
                "lfl_bracket_m": None, "lfl_model_m": d["raw"],
                "lfl_factored_m": d["factored"],
                "verdict": "no measurement installed"}
            continue
        a, traj, dur, win = _ffi(t)
        s_ = premise_summary(traj)
        lo, hi = brackets_from_arcs(ARCS, FFI[t][6])
        d = flammable_distance(traj, a, t_avg=win, t_release=float(dur))
        ffi[str(t)] = {
            "wind_10m_ms": FFI[t][2], "rate_kgs": FFI[t][0],
            "u_star_ms": a.u_star,
            "premise_ratio_max": s_["max"], "premise_violated": s_["violated"],
            "briggs_Lp_max": float(briggs_liftoff(traj, a).max()),
            "lfl_bracket_m": [lo, None if math.isinf(hi) else hi],
            "lfl_model_m": d["raw"], "lfl_factored_m": d["factored"],
            "verdict": verdict(d["raw"], (lo, hi))}
    out["ffi"] = ffi
    out["safety_factor"] = SAFETY_FACTOR
    out["lfl_in_bracket"] = sum(1 for v in ffi.values()
                                if v["verdict"] == "in")
    out["measurements_installed"] = any(v["lfl_bracket_m"]
                                        for v in ffi.values())
    out["critical_wind_ms"] = {f"{q}": critical_wind(q)
                               for q in (0.3, 1.0, 3.0, 9.5, 30.0)}

    # --- LNG pool set, all ten trials ------------------------------------
    lng = {}
    E = 116.93 / 657.0
    for name, st, u, zr, z0, q, dur, tav, obs in LNG_TRIALS:
        vals = {}
        for lbl, water in (("stock", water_backend()),
                           ("fixed", with_sublimation(water_backend()))):
            a = Atmosphere(u_ref=u, z_ref=zr, T=290.0, rh=50.0, z0=z0,
                           stability=st)
            traj, _ = run_dispersion(
                EvaporatingPool(substance=LNG, rate=q, area=q/E,
                                duration=float(dur)),
                a, LegacyThermo(LNG), water, x_max=1400.0, n_puff_steps=40)
            f = concentration_field(traj, a, z=1.0, t_avg=float(tav),
                                    t_release=float(dur))
            vals[lbl] = f.distance_to(0.05)
        vals["observed_m"] = float(obs)
        vals["change_pct"] = abs(vals["fixed"] - vals["stock"]) \
            / vals["stock"] * 100.0
        lng[name] = vals
    lng["max_change_pct"] = max(v["change_pct"] for v in lng.values()
                                if isinstance(v, dict))
    out["negative_control_lng_pool"] = lng

    # --- the defect's size on a dense gas, on the path it can reach --------
    # The published dense-gas validation runs on the legacy water backend,
    # which extrapolates Antoine below the triple point and was never
    # clamped, so the correction cannot reach it -- `lng` above is 0 by
    # construction. Run Burro 8 with the **CoolProp** water backend, which
    # does clamp, and the correction moves it by more than a tenth.
    a = Atmosphere(u_ref=1.94, z_ref=3.0, T=290.0, rh=50.0, z0=2e-4,
                   stability="E")
    src = dict(rate=116.93, area=116.93 / (116.93 / 657.0), duration=107.0)
    cp = {}
    for label, water in (("clamped", coolprop_water()),
                         ("corrected", with_sublimation(coolprop_water()))):
        traj, _ = run_dispersion(EvaporatingPool(substance=LNG, **src), a,
                                 LegacyThermo(LNG), water, x_max=1000.0,
                                 n_puff_steps=40)
        f = concentration_field(traj, a, z=1.0, t_avg=80.0, t_release=107.0)
        cp[label] = f.distance_to(0.05)
    same = abs(cp["clamped"] - cp["corrected"]) < 1e-9
    cp["change_pct"] = abs(cp["corrected"] - cp["clamped"]) \
        / cp["clamped"] * 100.0
    cp["upstream_already_corrected"] = bool(same)
    cp["note"] = ("the defect is not specific to hydrogen: Burro 8's cloud "
                  "runs 208 to 290 K and 25 of 58 trajectory points are "
                  "below the water triple point. Zero here means the "
                  "installed slabx has fixed it upstream (1.0.6+), not that "
                  "the defect was small. docs/42")
    out["defect_on_dense_gas_coolprop"] = cp

    # --- NASA: rise scaling and the residual ------------------------------
    nasa = {}
    for t, (u, ts, Tc, rh) in NASA.items():
        row = {"wind_ms": u, "rate_kgs": 5.7*70.8/ts}
        for lbl, ice, cpl, drg in (("baseline", False, False, False),
                                   ("water_only", True, False, False),
                                   ("width_only", False, True, False),
                                   ("both", True, True, False),
                                   ("both_plus_drag", True, True, True)):
            a = Atmosphere(u_ref=u, z_ref=10.0, T=Tc+273.15, rh=rh, z0=3e-3,
                           stability="D")
            wb = with_sublimation(coolprop_water()) if ice else coolprop_water()
            with plume_width_coupling(cpl), vertical_drag(drg):
                traj, _ = run_dispersion(
                    EvaporatingPool(substance=H2, rate=5.7*70.8/ts,
                                    area=math.pi*4.55**2, duration=float(ts)),
                    a, CoolPropThermo(H2, fluid="Hydrogen"), wb,
                    x_max=400.0, n_puff_steps=40)
            r = rise_scaling(traj)
            if lbl == "both":
                row.update({k: r[k] for k in
                            ("dlnB_dlnz", "dlnh_dlnz", "s",
                             "exponent_predicted", "width_ratio")})
                row["u_star_ms"] = a.u_star
                row["briggs_Lp_max"] = float(briggs_liftoff(traj, a).max())
                row["premise_ratio_max"] = premise_summary(traj)["max"]
            row[f"exponent_{lbl}"] = r["exponent"]
        nasa[str(t)] = row
    out["nasa"] = nasa
    out["prereg_plume_width"] = {
        "P_W1_band": [0.6, 0.9],
        # the registration's prediction is evaluated with the width coupling
        # alone and with the exploratory drag as well; both are reported
        # because the two answers differ and the paper must say which is
        # which. docs/31, prereg ADDENDUM 3.
        "P_W1_pass_width_only": sum(1 for v in nasa.values()
                                    if 0.6 <= v["exponent_both"] <= 0.9),
        "P_W1_pass_with_drag": sum(1 for v in nasa.values()
                                   if 0.6 <= v["exponent_both_plus_drag"]
                                   <= 0.9),
        "P_W2_band": [0.5, 2.0],
        "P_W2_pass": sum(1 for v in nasa.values()
                         if 0.5 <= v["width_ratio"] <= 2.0),
        "n_trials": len(nasa),
        # the scaling decomposition is measured on `both`, so the residual
        # is checked against `both`. Mixing the two configurations was an
        # error caught in review.
        "residual_errors_pct": sorted(
            abs(v["exponent_predicted"] / v["exponent_both"] - 1) * 100
            for v in nasa.values()),
        "note": "the width coupling alone reaches the band on none of the "
                "four; with the exploratory drag, on one. Neither is "
                "recorded as a pass: the outcome is dominated by the pool "
                "radius, which the original NASA paper does not report. "
                "docs/35 section 35.3"}

    # --- ground conduction against PRESLHY E3.4 Table 3 --------------------
    sub = substrate("concrete_cryogenic")
    table3 = [("first", 683.0, 716.0, 15.91), ("second", 856.0, 893.0, 15.73),
              ("third", 949.5, 1073.5, 10.95),
              ("fourth", 1180.5, 1295.5, 9.58)]
    periods, ratios = {}, []
    for label, t0, t_end, measured in table3:
        mid = 0.5 * (t0 + t_end) - 500.0
        f = ground_limited_flux(sub, 445000.0, 282.0, 20.0, mid)
        pred = f * 0.25 * 1e3
        ratios.append(pred / measured)
        periods[label] = {"t_mid_s": mid, "measured_gs": measured,
                          "predicted_gs": pred, "ratio": pred / measured,
                          "measured_flux_kgm2s": measured * 1e-3 / 0.25,
                          "measured_regression_mm_s":
                              measured * 1e-3 / 0.25 / 70.8 * 1e3}
    ratios.sort()
    out["ground_conduction_e34"] = {
        "substrate": {"conductivity": sub.conductivity,
                      "diffusivity": sub.diffusivity},
        "critical_heat_flux_W_m2": CRITICAL_HEAT_FLUX,
        "periods": periods,
        "median_ratio": 0.5 * (ratios[1] + ratios[2]),
        "range": [ratios[0], ratios[-1]],
        "report_stated_uncertainty_pct": 30.0}
    # the withdrawn "97 %": there is no single ratio, it runs with time
    e_lit = flux_from_regression(70.8, 1.0e-3)
    out["ground_flux_vs_literature"] = {
        "literature_1mm_s_kgm2s": e_lit,
        "ratio_at": {f"{t}": ground_limited_flux(sub, 445000.0, 288.15, 20.4,
                                                 t) / e_lit
                     for t in (60.0, 200.0, 500.0, 800.0)},
        "note": "no single ratio; see docs/28"}

    # --- the minimum factor the six FFI trials require --------------------
    need = [v["lfl_bracket_m"][0] / v["lfl_model_m"]
            for v in ffi.values()
            if v["lfl_bracket_m"] and v["lfl_model_m"] > 0]
    out["safety_factor_required"] = max(need) if need else None

    # --- critical wind, per stability class -------------------------------
    out["critical_wind"] = {
        "fit_range_kgs": list(CRITICAL_WIND_RANGE_KGS),
        "coefficients": {k: {"a": a, "b": b}
                         for k, (a, b) in CRITICAL_WIND_FIT.items()},
        "by_class_at": {f"{q}": {k: critical_wind(q, k)
                                 for k in CRITICAL_WIND_FIT}
                        for q in (0.3, 1.0, 9.5, 30.0)}}

    # --- air condensation onset against the flammable range ---------------
    out["air_condensation"] = {
        sp: condensation_onset(species=sp) for sp in ("N2", "O2")}

    # --- E3.5: does L_p order by wind rather than by rate? ----------------
    out["briggs_e35"] = _e35_briggs()

    # --- RR986: the same substrate properties on a different concrete -----
    out["ground_rr986"] = _rr986()
    return out


def _rr986():
    """
    RR986 Test 5, Figure 15, digitised. See scripts/rr986_ground.py.

    The E3.4 substrate properties are applied unadjusted to an outdoor slab.
    Two numbers matter: the drift of the inverted diffusivity across depth,
    which says whether the semi-infinite assumption holds, and the bias of the
    predicted temperature, which says whether the properties transfer.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_rr986_mod", _Path(__file__).resolve().parent / "rr986_ground.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    sub = substrate("concrete_cryogenic")
    inverted, residuals = {}, []
    for x, (T0, pts) in m.TRACES.items():
        vals = []
        for t, T in pts:
            if t > m.T_POOL_END:
                continue
            a = m.alpha_from(T, T0, x, t - m.T_POOL_START)
            if a is not None:
                vals.append(a)
            residuals.append(
                m.erfc_temperature(x, t - m.T_POOL_START, sub.diffusivity, T0)
                - T)
        if vals:
            vals.sort()
            inverted[f"{x*1e3:.0f}mm"] = {
                "median_alpha": vals[len(vals)//2],
                "vs_model": vals[len(vals)//2] / sub.diffusivity,
                "n": len(vals)}
    med = [v["median_alpha"] for v in inverted.values()]
    n = len(residuals)
    return {
        "source": "RR986 Figure 15, digitised; +-5 K, +-5 s",
        "model_alpha": sub.diffusivity,
        "inverted": inverted,
        "depth_drift": max(med) / min(med) if med else None,
        "temperature_bias_K": sum(residuals) / n,
        "temperature_rms_K": math.sqrt(sum(r*r for r in residuals) / n),
        "digitising_sigma_K": m.SIGMA_T_K,
        "verdict": "properties do not transfer; see docs/33"}


def _spearman(a, b):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    x, y = rank(a), rank(b)
    n = len(x); mx, my = sum(x) / n, sum(y) / n
    sxy = sum((p - mx) * (q - my) for p, q in zip(x, y))
    sxx = sum((p - mx) ** 2 for p in x); syy = sum((q - my) ** 2 for q in y)
    return sxy / math.sqrt(sxx * syy) if sxx and syy else float("nan")


def _e35_briggs():
    """
    PREREG_lh2_briggs_liftoff P-B1: L_p sorts by wind, not by rate.

    The release rates are the nominal table values. E3.5 also records a flow
    meter, whose peak and mean differ from the table by up to 30 % and 60 %
    respectively, and neither is obviously the right one -- the meter varies
    through the release. Running all three:

        nominal      n=17   L_p-wind -0.891   L_p-rate +0.213
        meter peak   n=17   L_p-wind -0.936   L_p-rate +0.199
        meter mean   n=17   L_p-wind -0.934   L_p-rate +0.309

    **The rate spans 14 to 298 g/s across the three choices and the ordering
    does not move.** That is the claim: L_p sorts by wind and not by rate, so
    a twentyfold change in the rate leaving the correlation at -0.89 to -0.94
    is the result rather than a robustness caveat.
    """
    import csv
    flow = {(25.4, 1): 0.1395, (12, 1): 0.1055, (25.4, 5): 0.298,
            (12, 5): 0.265, (6, 5): 0.095}
    tests = {"3.5.1": ("h", 0.5, 25.4, 1), "3.5.2": ("h", 0.5, 12, 1),
             "3.5.4": ("h", 1.5, 25.4, 1), "3.5.5": ("h", 1.5, 12, 1),
             "3.5.7": ("u", 0.5, 12, 1), "3.5.8": ("d", 0.5, 12, 1),
             "3.5.10": ("h", 0.5, 25.4, 5), "3.5.11": ("h", 0.5, 12, 5),
             "3.5.12": ("h", 0.5, 6, 5), "3.5.13": ("h", 1.5, 25.4, 5),
             "3.5.14": ("h", 1.5, 12, 5), "3.5.15": ("h", 1.5, 6, 5),
             "3.5.16": ("u", 0.5, 12, 5), "3.5.17": ("d", 0.5, 12, 5)}
    trial = {3: "3.5.1", 4: "3.5.2", 6: "3.5.7", 7: "3.5.8", 8: "3.5.8",
             10: "3.5.10", 11: "3.5.11", 12: "3.5.12", 13: "3.5.17",
             14: "3.5.16", 16: "3.5.4", 17: "3.5.5", 19: "3.5.4",
             20: "3.5.5", 22: "3.5.13", 23: "3.5.14", 24: "3.5.15"}
    # conditions from `slabx_lh2.trials`, which ships with the package
    from slabx_lh2.trials import E35
    rows, lp, u_v, q_v = {}, [], [], []
    for t, tr in sorted(E35.items()):
        ori = {"horizontal": "h", "vertical up": "u",
               "vertical down": "d"}[tr.orientation]
        bar = 5 if "5 barg" in tr.note else 1
        q, u = tr.rate_kg_s, tr.wind_m_s
        atm = Atmosphere(u_ref=u, z_ref=tr.wind_ref_height_m,
                         T=tr.temperature_C + 273.15, rh=tr.humidity_pct,
                         z0=tr.roughness_m, stability=tr.stability)
        if ori == "d":
            src = EvaporatingPool(substance=H2, rate=q, duration=120.0,
                                  area=math.pi * tr.pool_radius_m ** 2)
        else:
            src = HorizontalJet(substance=H2, rate=q, duration=120.0,
                                area=tr.area_m2,
                                liquid_fraction=1.0 - _flash(bar),
                                height=tr.release_height_m, T_source=20.37)
        with plume_width_coupling():
            traj, _ = run_dispersion(
                src, atm, CoolPropThermo(H2, fluid="Hydrogen"),
                with_sublimation(coolprop_water()), x_max=40.0,
                n_puff_steps=40)
        v = float(briggs_liftoff(traj, atm).max())
        rows[str(t)] = {"wind_ms": u, "rate_kgs": q, "u_star_ms": atm.u_star,
                        "briggs_Lp_max": v}
        lp.append(v); u_v.append(u); q_v.append(q)
    return {"trials": rows, "n": len(lp),
            "rank_corr_Lp_wind": _spearman(lp, u_v),
            "rank_corr_Lp_rate": _spearman(lp, q_v)}


def _flash(barg):
    p0 = barg * 1e5 + 101325.0
    h0 = _CP.PropsSI("H", "P", p0, "Q", 0, "Hydrogen")
    return float(_CP.PropsSI("Q", "P", 101325.0, "H", h0, "Hydrogen"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("section", nargs="?", choices=sorted(SECTIONS),
                    help="one section; omit to run all")
    ap.add_argument("--json", action="store_true",
                    help="also write results/results.json")
    args = ap.parse_args()
    for name in ([args.section] if args.section else list(SECTIONS)):
        SECTIONS[name]()
    if args.json:
        root = _Path(__file__).resolve().parent.parent / "results"
        root.mkdir(exist_ok=True)
        path = root / "results.json"
        with path.open("w", encoding="utf-8") as fh:
            _json.dump(collect(), fh, indent=2, sort_keys=False,
                       ensure_ascii=False)
        print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
