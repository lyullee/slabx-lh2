"""
Thermal diffusivity from the substrate temperature field.

Why not from the mass
---------------------
The evaporation rate and the diffusivity are related by one equation, so
choosing `alpha` to match a measured evaporation rate and then reporting that
the model reproduces that rate is circular. PRESLHY E3.4 avoided this for
concrete by taking `alpha` from the thermocouples and checking the mass
afterwards. This does the same for every substrate.

The method
----------
A semi-infinite solid held at `T_s` from `t = 0`:

    T(x, t) = T_0 + (T_s - T_0) erfc[ x / sqrt(4 alpha t) ]

so each thermocouple reading inverts to a diffusivity on its own:

    zeta = erfcinv[ (T - T_0) / (T_s - T_0) ]
    alpha = x^2 / (4 zeta^2 t)

Every depth and every time gives an estimate. **If the solid really is
semi-infinite with a fixed surface temperature, they all give the same
number**, and the spread across depths and times is the test -- a systematic
drift with depth means the geometry is wrong, and a drift with time means the
surface condition is not what was assumed.

Usage
-----
    python invert_alpha.py lh2_e34_traces.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

#: Substrate thermocouple -> depth below the surface [m].
DEPTH_M = {"TG96-00_K": 0.004, "TG91-00_K": 0.009, "TG86-00_K": 0.014,
           "TG46-00_K": 0.054, "TG02-00_K": 0.098}
#: Off-axis thermocouples at the same depth, used to check one-dimensionality.
OFF_AXIS = {"TG86-05_K": 0.014, "TG86-15_K": 0.014, "TG86-23_K": 0.014}
T_SURFACE = 20.0          # boiling LH2 at 1 bar
#: Readings within this of either end carry almost no information about alpha,
#: because erfc is flat there and the inversion amplifies noise without limit.
MARGIN_K = 8.0


def erfcinv(y: float) -> float:
    """Inverse complementary error function, by bisection on erfc."""
    if not 0.0 < y < 2.0:
        raise ValueError(f"erfc takes values in (0, 2), got {y!r}")
    lo, hi = -6.0, 6.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if math.erfc(mid) > y:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def alpha_from(T: float, T0: float, x: float, t: float,
               Ts: float = T_SURFACE) -> float | None:
    """
    Diffusivity [m2/s] implied by one reading, or ``None`` if uninformative.

    Discarded when the reading is within `MARGIN_K` of the surface or initial
    temperature: erfc is flat at both ends, so a tenth of a kelvin of noise
    moves `alpha` by orders of magnitude there.
    """
    if t <= 0.0 or x <= 0.0 or T0 <= Ts:
        return None
    if T <= Ts + MARGIN_K or T >= T0 - MARGIN_K:
        return None
    frac = (T - T0) / (Ts - T0)
    if not 0.0 < frac < 1.0:
        return None
    zeta = erfcinv(frac)
    if zeta <= 1e-6:
        return None
    return x * x / (4.0 * zeta * zeta * t)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("traces", nargs="?", default="lh2_e34_traces.csv")
    ap.add_argument("--t-min", type=float, default=30.0,
                    help="ignore times before this [s]")
    ap.add_argument("--t-max", type=float, default=600.0)
    args = ap.parse_args()

    path = Path(args.traces)
    if not path.exists():
        print(f"{path} not found; run extract_e34.py first")
        return 2
    rows = list(csv.DictReader(path.open(encoding="utf-8")))

    # initial substrate temperature: the first reading of each channel
    T0 = {}
    for r in rows:
        for ch in DEPTH_M:
            key = (r["run"], ch)
            v = r.get(ch)
            if key not in T0 and v:
                T0[key] = float(v)

    by_run = defaultdict(lambda: defaultdict(list))
    for r in rows:
        tg = r.get("t_ground_s")
        if not tg:
            continue
        t = float(tg)
        if not args.t_min <= t <= args.t_max:
            continue
        for ch, x in DEPTH_M.items():
            v = r.get(ch)
            if not v:
                continue
            a = alpha_from(float(v), T0.get((r["run"], ch), 282.0), x, t)
            if a is not None:
                by_run[r["run"]][ch].append(a)

    print(f"Diffusivity from the erfc solution, {args.t_min:.0f}"
          f" to {args.t_max:.0f} s after the surface reached 20 K")
    print(f"{'run':>11}{'substrate':>10}" +
          "".join(f"{ch.split('-')[0][2:] + ' mm':>11}" for ch in DEPTH_M) +
          f"{'median':>12}{'spread':>9}")
    subs = {r["run"]: r["substrate"] for r in rows}
    out = {}
    for run, chans in by_run.items():
        cells, everything = [], []
        for ch in DEPTH_M:
            v = chans.get(ch, [])
            everything += v
            cells.append(f"{st.median(v):.2e}" if v else "-")
        if not everything:
            continue
        med = st.median(everything)
        lo, hi = min(everything), max(everything)
        out[run] = med
        print(f"{run:>11}{subs[run]:>10}" +
              "".join(f"{c:>11}" for c in cells) +
              f"{med:>12.3e}{hi / lo:>8.0f}x")

    print()
    print("Depth is the diagnostic. If the solid is semi-infinite and the")
    print("surface is held at 20 K, every depth gives the same number; a")
    print("drift with depth means one of those is false.")
    print()
    print("For reference, PRESLHY E3.4 report 2.5e-7 m2/s for their concrete,")
    print("derived the same way from the same thermocouples.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
