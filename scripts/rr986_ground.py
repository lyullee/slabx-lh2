"""
RR986 Test 5: the concrete temperature field, against semi-infinite conduction.

Why this dataset
----------------
Document 29 established that the PRESLHY E3.4 box is **not** a semi-infinite
solid -- the bed is 100 mm deep on Styrofoam, and inverting the erfc solution
at 4, 9, 14, 54 and 98 mm gives diffusivities that drift by a factor of four
with depth. That is a property of the apparatus, not of the model.

RR986 released onto an **outdoor concrete slab**, which is much closer to the
semi-infinite case a real spill sees. Three thermocouples at 10, 20 and 30 mm
below the surface, on a slab with no insulated back face within reach of the
cooling front over the 250 s of the release.

**Nothing is adjusted.** The substrate properties are
`slabx_lh2.pool.substrate("concrete_cryogenic")`, which came from E3.4's
thermocouples, and the test is whether they predict a different experiment.

The data
--------
Read from Figure 15 of RR986 (Royle & Willoughby 2014), the trace file
`lh2unig051.xls`. Digitised by eye from the published figure at roughly 20 s
intervals; **the uncertainty is about +-5 K in temperature and +-5 s in time**,
which is stated here because it bounds what the comparison can show.

Two features of the figure govern how it is read.

**The initial temperature is 233 K, not ambient.** RR986 gives 10.3 C for the
test, and the embedded thermocouples read 50 K below that before the release.
Whether that is a calibration offset -- PRESLHY found exactly this on the same
kind of sheathed type-K probe -- or concrete left cold by an earlier release
the same day cannot be settled from the figure. **`T_0` is therefore taken
from each trace's own plateau**, which is what the erfc inversion needs and
which cancels a constant offset to first order.

**The surface is held at liquid temperature only while the pool is there.**
The valve opens at about 245 s and closes at 490 s; Figure 16 shows the pool
thermocouples dropping to about 18 K at 237 s and staying there until 490 s.
So the conduction window is 237 to 490 s, and everything after is the ground
warming back up with no pool on it.

    python scripts/rr986_ground.py
"""

from __future__ import annotations

import math
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from slabx_lh2.pool import ground_limited_flux, substrate  # noqa: E402

#: Surface temperature while the pool is present [K]; Figure 16 plateau.
T_SURFACE = 19.0
#: Pool established, from the Figure 16 step [s].
T_POOL_START = 237.0
#: Valve closed [s]; after this the surface is no longer held cold.
T_POOL_END = 490.0
#: Digitising uncertainty, stated so it can be carried into the conclusion.
SIGMA_T_K = 5.0

#: depth [m] -> (T_0 [K], [(t [s], T [K]), ...]) read from Figure 15.
TRACES = {
    0.010: (233.0, [
        (285, 233), (300, 215), (310, 197), (320, 190), (340, 165),
        (360, 145), (380, 130), (400, 120), (420, 110), (440, 100),
        (460, 92), (480, 85),
    ]),
    0.020: (233.0, [
        (310, 233), (330, 228), (350, 215), (370, 200), (390, 185),
        (410, 170), (430, 155), (450, 145), (470, 135), (490, 128),
    ]),
    0.030: (236.0, [
        (355, 236), (380, 232), (400, 226), (420, 218), (440, 208),
        (460, 198), (480, 188),
    ]),
}


def erfcinv(y: float) -> float:
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
               Ts: float = T_SURFACE, margin: float = 8.0):
    """Diffusivity implied by one reading, or None where erfc is flat."""
    if t <= 0.0 or T <= Ts + margin or T >= T0 - margin:
        return None
    frac = (T - T0) / (Ts - T0)
    if not 0.0 < frac < 1.0:
        return None
    zeta = erfcinv(frac)
    return x * x / (4.0 * zeta * zeta * t) if zeta > 1e-6 else None


def erfc_temperature(x: float, t: float, alpha: float, T0: float,
                     Ts: float = T_SURFACE) -> float:
    if t <= 0.0:
        return T0
    return T0 + (Ts - T0) * math.erfc(x / math.sqrt(4.0 * alpha * t))


def main() -> int:
    sub = substrate("concrete_cryogenic")
    alpha_model = sub.diffusivity

    print("RR986 Test 5, Figure 15 -- concrete at 10, 20 and 30 mm")
    print(f"  pool present {T_POOL_START:.0f} to {T_POOL_END:.0f} s, "
          f"surface held at {T_SURFACE:.0f} K")
    print(f"  substrate from E3.4, unadjusted: alpha = {alpha_model:.3e} m2/s,"
          f" k = {sub.conductivity:.2f} W/mK")

    # ---- 1. does the depth drift that broke E3.4 appear here? -----------
    print("\n1. Diffusivity inverted from each depth")
    print(f"{'depth':>8}{'n':>4}{'median alpha':>15}{'range':>22}"
          f"{'vs model':>10}")
    inverted = {}
    for x, (T0, pts) in TRACES.items():
        vals = []
        for t, T in pts:
            if t > T_POOL_END:
                continue
            a = alpha_from(T, T0, x, t - T_POOL_START)
            if a is not None:
                vals.append(a)
        if not vals:
            print(f"{x*1e3:>7.0f}mm{0:>4}{'-':>15}")
            continue
        inverted[x] = st.median(vals)
        print(f"{x*1e3:>7.0f}mm{len(vals):>4}{st.median(vals):>15.3e}"
              f"{f'{min(vals):.2e} - {max(vals):.2e}':>22}"
              f"{st.median(vals)/alpha_model:>10.2f}")
    if len(inverted) > 1:
        lo, hi = min(inverted.values()), max(inverted.values())
        print(f"\n   drift across depth: {hi/lo:.2f}x"
              f"   (E3.4's insulated box: 4.3x over 4 to 54 mm)")

    # ---- 2. predict the traces with the unadjusted properties -----------
    print("\n2. Temperature predicted with the E3.4 properties, unadjusted")
    print(f"{'depth':>8}{'t [s]':>8}{'measured':>10}{'predicted':>11}"
          f"{'diff [K]':>10}")
    residuals = []
    for x, (T0, pts) in TRACES.items():
        for t, T in pts:
            if t > T_POOL_END:
                continue
            pred = erfc_temperature(x, t - T_POOL_START, alpha_model, T0)
            residuals.append(pred - T)
            print(f"{x*1e3:>7.0f}mm{t:>8.0f}{T:>10.0f}{pred:>11.1f}"
                  f"{pred - T:>+10.1f}")
    rms = math.sqrt(sum(r * r for r in residuals) / len(residuals))
    bias = sum(residuals) / len(residuals)
    print(f"\n   n = {len(residuals)},  bias {bias:+.1f} K,  RMS {rms:.1f} K")
    print(f"   digitising uncertainty is about +-{SIGMA_T_K:.0f} K")

    # ---- 3. what the model says about the evaporation -------------------
    print("\n3. Evaporation implied by the same properties")
    print(f"{'t [s]':>8}{'flux [kW/m2]':>15}{'regression [mm/s]':>19}")
    for t in (30.0, 60.0, 120.0, 253.0):
        f = ground_limited_flux(sub, 445e3, 233.0, T_SURFACE, t)
        print(f"{t:>8.0f}{f*445e3/1e3:>15.1f}{f/70.8*1e3:>19.2f}")
    print("   RR986 reports a pool of constant extent, which is the "
          "equilibrium\n   the pool-radius calculation assumes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
