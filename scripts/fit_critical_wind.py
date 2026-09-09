"""Regenerate the pool-source critical-wind screening curves.

The post-run applicability diagnostic is the model-state quantity
``Pi = max(w_c / u)``.  This script finds the 10 m wind speed at which Pi=1
for four release rates and each Pasquill class, then fits

    u_crit = a q**b.

The fit is a compact pre-run screen of the model's own coordinate boundary;
it is not an experimental lift-off correlation.  Run from the repository root:

    python scripts/fit_critical_wind.py

By default the evaluated plume-width coupling is active.  The raw bisection
points and fitted coefficients are written to ``paper_results``.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from contextlib import nullcontext
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from slabx.core.plume import run_dispersion
from slabx.core.source import EvaporatingPool
from slabx.submodels.atmosphere import Atmosphere
from slabx.thermo.base import Substance
from slabx.thermo.coolprop import CoolPropThermo, coolprop_water

from slabx_lh2.diagnostics import CRITICAL_WIND_FIT, premise_summary
from slabx_lh2.plume_width import plume_width_coupling
from slabx_lh2.water_ice import with_sublimation


H2 = Substance(
    name="H2", mw=0.002016, cp_vapour=14300.0, cp_liquid=9800.0,
    dh_vap=445000.0, T_boil=20.3, rho_liquid=70.8,
)
RATES = (0.1, 1.0, 9.5, 30.0)
STABILITIES = tuple("ABCDEF")
POOL_EVAPORATION_FLUX = 70.8e-3  # kg m-2 s-1: 1 mm s-1 regression


def premise_ratio(rate: float, wind: float, stability: str,
                  *, width_coupling: bool = True) -> float:
    """Run one pool case and return ``max(w_c/u)``."""
    atmosphere = Atmosphere(
        u_ref=wind, z_ref=10.0, T=288.15, rh=50.0, z0=3e-3,
        stability=stability,
    )
    source = EvaporatingPool(
        substance=H2, rate=rate, area=rate / POOL_EVAPORATION_FLUX,
        duration=300.0,
    )
    thermo = CoolPropThermo(H2, fluid="Hydrogen")
    water = with_sublimation(coolprop_water())
    context = plume_width_coupling() if width_coupling else nullcontext()
    with context:
        trajectory, _ = run_dispersion(
            source, atmosphere, thermo, water, x_max=400.0,
            n_puff_steps=40,
        )
    return float(premise_summary(trajectory)["max"])


def bisect_boundary(rate: float, stability: str, *, width_coupling: bool,
                    ratio_tolerance: float = 2e-4,
                    max_iterations: int = 40) -> dict[str, float | int | str]:
    """Find wind speed where ``max(w_c/u)=1`` with a bracketed bisection."""
    low, high = 0.25, 15.0
    r_low = premise_ratio(rate, low, stability,
                          width_coupling=width_coupling)
    r_high = premise_ratio(rate, high, stability,
                           width_coupling=width_coupling)
    while r_low <= 1.0 and low > 0.02:
        low *= 0.5
        r_low = premise_ratio(rate, low, stability,
                              width_coupling=width_coupling)
    while r_high >= 1.0 and high < 60.0:
        high *= 1.5
        r_high = premise_ratio(rate, high, stability,
                               width_coupling=width_coupling)
    if not (r_low > 1.0 and r_high < 1.0):
        raise RuntimeError(
            f"could not bracket Pi=1 for class={stability}, rate={rate}: "
            f"Pi({low})={r_low}, Pi({high})={r_high}"
        )

    middle = float("nan")
    r_middle = float("nan")
    for iteration in range(1, max_iterations + 1):
        middle = 0.5 * (low + high)
        r_middle = premise_ratio(rate, middle, stability,
                                 width_coupling=width_coupling)
        if abs(r_middle - 1.0) <= ratio_tolerance:
            break
        if r_middle > 1.0:
            low, r_low = middle, r_middle
        else:
            high, r_high = middle, r_middle

    return {
        "stability": stability,
        "rate_kg_s": rate,
        "u_crit_m_s": middle,
        "premise_ratio": r_middle,
        "iterations": iteration,
        "bracket_low_m_s": low,
        "bracket_high_m_s": high,
    }


def fit(rows: list[dict[str, float | int | str]]) -> dict[str, dict[str, float]]:
    """Fit log(u)=log(a)+b log(q), with residual diagnostics."""
    result: dict[str, dict[str, float]] = {}
    for stability in STABILITIES:
        selected = [row for row in rows if row["stability"] == stability]
        q = np.asarray([float(row["rate_kg_s"]) for row in selected])
        u = np.asarray([float(row["u_crit_m_s"]) for row in selected])
        b, log_a = np.polyfit(np.log(q), np.log(u), 1)
        a = math.exp(float(log_a))
        predicted = a * q ** float(b)
        relative = np.abs(predicted / u - 1.0)
        frozen_a, frozen_b = CRITICAL_WIND_FIT[stability]
        result[stability] = {
            "a": a,
            "b": float(b),
            "max_fit_relative_error": float(relative.max()),
            "frozen_a": frozen_a,
            "frozen_b": frozen_b,
            "a_relative_difference": a / frozen_a - 1.0,
            "b_absolute_difference": float(b) - frozen_b,
        }
    return result


def make_payload(
    rows: list[dict[str, float | int | str]], *, width_coupling: bool,
) -> dict[str, object]:
    """Assemble the frozen fit record from evaluated bisection points."""
    return {
        "definition": "u_crit is the 10 m wind at max(w_c/u)=1",
        "source": {
            "type": "evaporating pool",
            "rates_kg_s": list(RATES),
            "pool_evaporation_flux_kg_m2_s": POOL_EVAPORATION_FLUX,
            "duration_s": 300.0,
        },
        "atmosphere": {
            "temperature_K": 288.15, "relative_humidity_pct": 50.0,
            "roughness_m": 0.003, "wind_reference_height_m": 10.0,
        },
        "width_coupling": width_coupling,
        "fit": "ordinary least squares in log(u)-log(q)",
        "coefficients": fit(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--without-width-coupling", action="store_true",
        help="diagnostic comparison only; the manuscript configuration uses it",
    )
    parser.add_argument(
        "--check-existing", action="store_true",
        help=("check the saved width-coupled fit against the public constants; "
              "recompute it in memory when the private paper result is absent"),
    )
    parser.add_argument(
        "--out-dir", type=Path, default=ROOT / "paper_results",
    )
    args = parser.parse_args()
    width_coupling = not args.without_width_coupling

    if args.check_existing:
        if args.without_width_coupling:
            parser.error("--check-existing refers only to the evaluated width-coupled fit")
        saved = args.out_dir / "critical_wind_fit.json"
        if saved.exists():
            payload = json.loads(saved.read_text(encoding="utf-8"))
            source_label = str(saved)
        else:
            rows = [
                bisect_boundary(rate, stability, width_coupling=True)
                for stability in STABILITIES for rate in RATES
            ]
            payload = make_payload(rows, width_coupling=True)
            source_label = "an in-memory recomputation (private result absent)"
        if payload.get("width_coupling") is not True:
            raise RuntimeError("saved critical-wind fit is not width-coupled")
        for stability in STABILITIES:
            item = payload["coefficients"][stability]
            expected_a, expected_b = CRITICAL_WIND_FIT[stability]
            if not math.isclose(float(item["a"]), expected_a, abs_tol=1e-6):
                raise RuntimeError(
                    f"class {stability} a differs: {item['a']} != {expected_a}"
                )
            if not math.isclose(float(item["b"]), expected_b, abs_tol=1e-6):
                raise RuntimeError(
                    f"class {stability} b differs: {item['b']} != {expected_b}"
                )
        print(f"width-coupled critical-wind fit from {source_label} "
              "matches CRITICAL_WIND_FIT")
        return 0

    rows = [
        bisect_boundary(rate, stability, width_coupling=width_coupling)
        for stability in STABILITIES for rate in RATES
    ]
    payload = make_payload(rows, width_coupling=width_coupling)
    coefficients = payload["coefficients"]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "" if width_coupling else "_without_width_coupling"
    csv_path = args.out_dir / f"critical_wind_bisection{suffix}.csv"
    json_path = args.out_dir / f"critical_wind_fit{suffix}.json"

    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"wrote {csv_path}")
    print(f"wrote {json_path}")
    print("class          a          b    max fit err   delta a   delta b")
    for stability in STABILITIES:
        item = coefficients[stability]
        print(
            f"{stability:>5} {item['a']:10.6f} {item['b']:10.6f} "
            f"{100*item['max_fit_relative_error']:11.3f}% "
            f"{100*item['a_relative_difference']:+8.3f}% "
            f"{item['b_absolute_difference']:+9.6f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
