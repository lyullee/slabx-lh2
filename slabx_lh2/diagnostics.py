"""
Diagnostics: when the model is outside its own premises, and when a cloud
lifts.

Two quantities, neither of which changes a prediction.  Both are reported.

`premise_ratio` -- the bent-over premise
---------------------------------------
SLAB's plume mode marches in `x`, which presumes the cloud is carried
downwind.  Its diagnostic is ``w_c / u``: above 1 the cloud rises faster than
it advects, and the marching variable is no longer a coordinate along the
cloud.  On NASA White Sands Test 6 it reaches 3.68, a rise angle of 75 degrees;
on FFI Test 4 it stays at 0.030.

The boundary in release rate and wind, fitted to the model's own output over a
pool source at stability D:

    w_c/u ~ q^0.31 / u^2.05      =>      u_crit = a q^b        [m/s, kg/s]

with `a` and `b` per stability class in `CRITICAL_WIND_FIT`; class D is
2.611924 q^0.133865. The coefficients are regenerated with the complete
width-coupled 0.1.3 configuration. Earlier figures in the project record were
obtained before that calculation path was frozen and are superseded.

**Wind dominates.** A hundredfold change in rate moves the critical wind by a
factor of two.  Stability moves it by about 2.5: 2.5 m/s at B, 3.5 at D, 6.2 at F
for 9.5 kg/s -- and that dependence inherits the stability-response deficiency
of document 03 section 3.7.

This is not specific to slabx.  Briggs's bent-over plume formula rests on the
same premise and is equally invalid there.

`briggs_liftoff` -- Briggs's lift-off parameter
-----------------------------------------------
Briggs (1973), *Lift-off of buoyant gas initially on the ground*, ATDL
Contribution 87, as set out by Hanna (2022):

    L_p = g H (rho_a - rho_p) / rho_a / u*^2

with lift-off proposed at ``L_p > 20``, "with an uncertainty of at least a
factor of two".  Hanna, Briggs & Chang (1998) added, for the grounded case,

    F** = g H (rho_a - rho_p) / (rho_a U^2)
    C(F**) / C(0) = exp(-6 F**^0.4)

fitted to Hall's wind-tunnel series on broad flat sources.

**The denominator is the point.** `u*^2`, not `U^3`.  The friction velocity
carries roughness and stability; the mean wind does not.  An earlier attempt
using Hall & Walker's `F/(W u^3)` had no discriminating power at all -- below
threshold where clouds lifted, above it where they did not.

`L_p` orders every dataset tested correctly:

    FFI    six trials      the one that lifted is 29.0, the rest 2.3 - 11.7
    E3.5   seventeen       rank correlation with wind -0.891, with rate +0.213
    RR986  four, fixed q   52.5, 13.6, 6.7, 3.8 -- monotone in wind
    NASA   four            rank correlation with wind -1.000

**The threshold does not transfer across scale.** It separates the three sets
spanning 0.07 to 0.83 kg/s and fails on NASA at 10 to 17 kg/s, where all four
trials exceed it including the one whose flammable cloud sat at 0.3 m.  So
`L_p` is carried as an ordering variable and is not used as a gate.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

__all__ = ["GRAVITY", "BRIGGS_THRESHOLD", "premise_ratio", "premise_summary",
           "critical_wind", "CRITICAL_WIND_FIT", "CRITICAL_WIND_RANGE_KGS",
           "applicability", "briggs_liftoff", "grounded_thinning",
           "rise_scaling"]

GRAVITY = 9.80665
#: Briggs (1973), stated uncertainty a factor of two.
BRIGGS_THRESHOLD = 20.0
#: Below this a friction velocity is not physically meaningful and the
#: `L_p` denominator would amplify rounding noise without limit.
_U_STAR_FLOOR = 1e-3


def _positive_deficit(traj, atm) -> np.ndarray:
    rho = np.asarray(traj.rho, dtype=float)
    rho_a = float(atm.rho)
    if rho_a <= 0.0:
        raise ValueError("ambient density must be > 0")
    d = (rho_a - rho) / rho_a
    return np.where(np.isfinite(d) & (d > 0.0), d, 0.0)


def premise_ratio(traj, *, downwind_only: bool = True) -> np.ndarray:
    """
    ``w_c / u`` along the trajectory.

    `downwind_only` masks the source region, where `x` is negative and the
    ratio has no meaning; masked points come back as 0.
    """
    w = np.asarray(traj.w_c, dtype=float)
    u = np.asarray(traj.u, dtype=float)
    r = np.divide(w, u, out=np.zeros_like(w), where=np.abs(u) > 1e-12)
    r = np.where(np.isfinite(r), r, 0.0)
    if downwind_only:
        r = np.where(np.asarray(traj.x, dtype=float) > 0.0, r, 0.0)
    return r


def premise_summary(traj, *, threshold: float = 1.0) -> dict[str, Any]:
    """``{max, x_at_max, angle_deg, violated, n_violating, x_first, x_last}``."""
    r = premise_ratio(traj)
    x = np.asarray(traj.x, dtype=float)
    if r.size == 0 or not np.any(np.isfinite(r)):
        return {"max": float("nan"), "x_at_max": float("nan"),
                "angle_deg": float("nan"), "violated": False,
                "n_violating": 0, "x_first": None, "x_last": None}
    i = int(np.argmax(r))
    bad = np.where(r > threshold)[0]
    return {
        "max": float(r[i]),
        "x_at_max": float(x[i]),
        "angle_deg": math.degrees(math.atan(max(float(r[i]), 0.0))),
        "violated": bool(bad.size),
        "n_violating": int(bad.size),
        "x_first": float(x[bad[0]]) if bad.size else None,
        "x_last": float(x[bad[-1]]) if bad.size else None,
    }


#: ``u_crit = a q^b`` per Pasquill class, bisected on the model's own
#: ``max w_c/u`` at 0.1, 1.0, 9.5 and 30 kg/s for a pool source and fitted in
#: log-log.  These describe where the **formulation's
#: premise** fails; they are not an experimental correlation and must not be
#: quoted as one.  See `docs/26_RESULTS_REGISTER.md` section 26.5.
CRITICAL_WIND_FIT: dict[str, tuple[float, float]] = {
    "A": (1.827780, 0.113448), "B": (1.918922, 0.116222),
    "C": (2.098340, 0.120398), "D": (2.611924, 0.133865),
    "E": (3.771833, 0.127441), "F": (4.744319, 0.118767),
}
#: The range the fit was performed over. Outside it the form is extrapolation.
CRITICAL_WIND_RANGE_KGS = (0.1, 30.0)


def critical_wind(rate: float, stability: str = "D") -> float:
    """
    Wind speed [m/s] below which the model's own ``w_c/u`` exceeds 1 for a
    pool release of `rate` kg/s.

    ``u_crit = a q^b`` with the coefficients of `CRITICAL_WIND_FIT`, fitted to
    slabx output rather than to observations.

    **This is a screening approximation, not the diagnostic.** The diagnostic
    is `premise_summary`, which reads the model's actual state. `critical_wind`
    exists so that a monitoring system can decide whether to run at all, from
    the release rate and wind alone, before integrating anything. Where the two
    disagree, the diagnostic is right.
    """
    if rate <= 0.0:
        raise ValueError(f"rate must be > 0, got {rate!r}")
    key = str(stability).strip().upper()
    if key not in CRITICAL_WIND_FIT:
        raise ValueError(
            f"unknown stability class {stability!r}; "
            f"have {sorted(CRITICAL_WIND_FIT)}")
    a, b = CRITICAL_WIND_FIT[key]
    return a * rate ** b


def applicability(traj, *, marginal: float = 0.5,
                  threshold: float = 1.0) -> dict[str, Any]:
    """
    Legacy three-band display status for a completed run.

    ``{status, premise_ratio, angle_deg, x_at_max, reason, fallback_required}``
    with `status` one of ``VALID``, ``MARGINAL``, ``OUT_OF_SCOPE``.

    ``OUT_OF_SCOPE`` is the scientific routing result used by the manuscript:
    the marching variable has stopped being the dominant coordinate and the
    endpoint is withheld.  ``VALID`` and ``MARGINAL`` are retained for 0.1.3
    interface compatibility; neither is a universal model-validity claim.

    The band between `marginal` and `threshold` has no independent physical or
    experimental evidence.  It exists only as a legacy display warning.  Use
    the continuous ``premise_ratio`` and the binary ``> threshold`` route in
    scientific analyses.
    """
    if not 0.0 < marginal <= threshold:
        raise ValueError(
            f"need 0 < marginal <= threshold, got {marginal!r}, {threshold!r}")
    s = premise_summary(traj, threshold=threshold)
    r = s["max"]
    if not math.isfinite(r):
        status = "OUT_OF_SCOPE"
        reason = "the rise-to-advection ratio is not finite"
    elif r > threshold:
        status = "OUT_OF_SCOPE"
        reason = (f"rise-to-advection ratio {r:.2f} exceeds {threshold:g} at "
                  f"x = {s['x_at_max']:.1f} m; the cloud rises faster than it "
                  f"advects and the downwind-marching formulation no longer "
                  f"describes it")
    elif r > marginal:
        status = "MARGINAL"
        reason = (f"rise-to-advection ratio {r:.2f} is within a factor of two "
                  f"of the premise limit")
    else:
        status = "VALID"
        reason = f"rise-to-advection ratio {r:.2f} is well inside the premise"
    return {"status": status, "premise_ratio": r, "angle_deg": s["angle_deg"],
            "x_at_max": s["x_at_max"], "reason": reason,
            "fallback_required": status == "OUT_OF_SCOPE"}


def briggs_liftoff(traj, atm) -> np.ndarray:
    """
    Briggs's lift-off parameter ``L_p`` along the trajectory.

    Zero wherever the cloud is denser than ambient.  Raises if the friction
    velocity is too small to square meaningfully, rather than returning a
    number dominated by rounding.
    """
    u_star = float(getattr(atm, "u_star", 0.0))
    if not math.isfinite(u_star) or u_star < _U_STAR_FLOOR:
        raise ValueError(
            f"friction velocity {u_star!r} is below {_U_STAR_FLOOR}; L_p is "
            f"1/u*^2 and would be meaningless. Check the wind speed and "
            f"roughness.")
    h = np.asarray(traj.h, dtype=float)
    return GRAVITY * h * _positive_deficit(traj, atm) / (u_star * u_star)


def dimensionless_buoyancy_flux(traj, atm) -> np.ndarray:
    """``F** = g H (rho_a - rho) / (rho_a U^2)``, Hanna, Briggs & Chang (1998)."""
    h = np.asarray(traj.h, dtype=float)
    U = np.asarray(traj.u_ambient_mean, dtype=float)
    U = np.where(np.isfinite(U) & (U > 1e-9), U, np.nan)
    return GRAVITY * h * _positive_deficit(traj, atm) / (U * U)


def grounded_thinning(f_star_star) -> np.ndarray:
    """
    ``C(F**) / C(0) = exp(-6 F**^0.4)`` -- the ground-level concentration ratio
    for a buoyant plume that has not yet lifted off.

    Hanna, Briggs & Chang (1998), fitted to Hall's wind-tunnel data.  Reported,
    not applied: it was registered as a prediction in
    `PREREG_lh2_briggs_liftoff` and failed against the E3.5 arc decay ratio,
    on a target that turned out to be censored by the 4 vol% sensor ceiling.
    """
    f = np.asarray(f_star_star, dtype=float)
    f = np.where(np.isfinite(f) & (f > 0.0), f, 0.0)
    return np.exp(-6.0 * np.power(f, 0.4))


def rise_scaling(traj, *, x_lo: float = 10.0, x_hi: float = 100.0,
                 beta: float = 0.4) -> dict[str, Any]:
    """
    Why a lofted cloud rises as fast as it does, decomposed.

    A bent-over buoyant plume rises as ``x^(2/3)`` because its cross-section
    grows in **both** directions with height.  Writing the rise as

        dz/dx = Gw / (R u),     Gw ~ x,     R = rho u B h ~ z^s

    gives ``z^(s+1) ~ x^2``, so

        n = 2 / (s + 1),        s = dlnB/dlnz + dlnh/dlnz

    Briggs is ``s = 2``: both semi-axes proportional to ``z``.  The width
    coupling of `slabx_lh2.plume_width` addresses ``B`` only, and only
    partially -- the gravity-spreading and ground-entrainment terms in EQ 7
    remain and dilute it.  Measured on the four NASA trials with both modules
    active, ``dlnB/dlnz`` reaches 0.39 to 0.59 and ``dlnh/dlnz`` 0.23 to 0.49,
    for ``s`` of 0.62 to 1.01 and a predicted exponent of 0.99 to 1.24 -- which
    matches the fitted exponent to within 6 % (3.0, 3.1, 5.7 and 5.9 %).

    **So the residual is not unexplained.** The depth is not coupled to the
    rise at all, and the width only partway. Returns
    ``{exponent, dlnB_dlnz, dlnh_dlnz, s, exponent_predicted, width_ratio}``.
    """
    x = np.asarray(traj.x, dtype=float)
    z = np.asarray(traj.z_c, dtype=float)
    B = np.asarray(traj.b_half, dtype=float)
    h = np.asarray(traj.h, dtype=float)
    k = (x > x_lo) & (x < x_hi) & (z > 0.0) & (B > 0.0) & (h > 0.0)
    if k.sum() < 4:
        raise ValueError(
            f"only {int(k.sum())} lofted points between {x_lo} and {x_hi} m; "
            f"the fit needs at least four. Is the cloud lofting at all?")
    n = float(np.polyfit(np.log(x[k]), np.log(z[k]), 1)[0])
    nB = float(np.polyfit(np.log(z[k]), np.log(B[k]), 1)[0])
    nh = float(np.polyfit(np.log(z[k]), np.log(h[k]), 1)[0])
    s = nB + nh
    zz = float(np.interp(x_hi, x, z))
    BB = float(np.interp(x_hi, x, B))
    return {"exponent": n, "dlnB_dlnz": nB, "dlnh_dlnz": nh, "s": s,
            "exponent_predicted": 2.0/(s + 1.0) if s > -1.0 else float("nan"),
            "width_ratio": BB/max(beta*zz, 1e-12)}
