"""
A passive-dispersion ceiling on the cloud depth.

    from slabx_lh2.depth_cap import depth_cap

    with depth_cap():
        traj, used = run_dispersion(source, atm, emission, water)

**Three registrations, all rejected.** The premise is false: a cloud *can* be
thicker than a passively dispersing layer, because near the source it has
gravity-driven spreading and shear of its own. Lowering the ceiling to the
model's own passive asymptote made the dense-gas error worse, not better,
which is the signature of a constraint that is removing real physics.

Kept for `sigma_z`, for `TOP_HAT_FACTOR` -- both of which are measurements
about the formulation that are useful on their own -- and so that a fourth
attempt is not made.

**Earlier framing, superseded:** The passive ceiling destroys the dense-gas
validation: `sigma_z(x)` goes to zero at the source, so a pool source metres
deep is crushed to centimetres in its first step. LNG moves by 36 % and
Prairie Grass is no longer bit-identical.

The module is kept so the attempt is not repeated and because `fired_count`
below exists to prevent the failure that hid it for a whole registration.

**Two registrations.** `PREREG_lh2_depth_cap` capped the depth for the whole
trajectory and was **rejected**; `PREREG_lh2_depth_plume` adds the second
regime, in which the depth grows with the rise once the cloud lofts.

The first registration, and why it failed:

Registered in `docs/prereg/PREREG_lh2_depth_cap.md` and run;
NC3 failed on three of four downward trials and P-D4 failed on every trial.
It is kept because the failure is informative and because someone will
otherwise try it again.

**What it does and why that is not enough.** Capping the depth does raise the
near-field concentration -- the quantity it targets responds, and on the two
horizontal trials one of them reaches the registered band. But the cap holds
`h` fixed while `z_c` keeps growing, so the cloud becomes a thin ribbon that
climbs out of the sensor plane: two trials read zero at every arc afterwards.

**The depth and the rise are one term.** `docs/27` measured
`dlnh/dlnz = 0.23 to 0.49` against a required 1.0, and this cap drives it
further from 1 rather than towards it.

Why
---
At 30 m on FFI test 6 the modelled cloud is 8.1 m wide and 7.8 m deep. A
Pasquill-Gifford passive layer at the same distance is 7.2 m and 2.6 m: **the
width is right to 10 % and the depth is three times too large**, and that
alone is the factor of 2.6 by which the horizontal-jet maximum is
under-predicted. The same mass spread through three times the depth gives a
third of the concentration.

It is the same deficit that `slabx_lh2.diagnostics.rise_scaling` measured
independently on the NASA trials, where `dlnh/dlnz` is 0.23 to 0.49 against a
required 1.0.

The ceiling is physical rather than fitted: **a layer cannot be thicker than
the turbulence can mix it.** Whatever the entrainment closure computes, the
depth at a given distance is bounded by what passive dispersion produces,
because passive dispersion is the fastest mixing available once the cloud has
lost its own buoyancy-driven and shear-driven mixing.

The seam
--------
**The closure has no downwind coordinate.** `CloudLocal` carries the depth,
the width and the velocities but not `x`, and `Trajectory.sigma_z` is derived
from the depth (`0.5 h / sqrt(3)`), so using it as a ceiling would be
circular.

The coordinate does exist in the caller: `slabx.core.plume._build_stage`
takes `x` as a keyword argument and calls `entrainment(cl, atm, fr, ...)`
from that scope. This module reads `x` from the calling frame, walking up a
few frames so that it also works from `_initial_state`, where the position is
`dx` from the source origin.

**That is a deliberate and fragile choice, and it is documented as such.**
It is a read of one attribute from a named local in a known caller; it does
not mutate anything and it fails closed -- if the frame or the attribute is
not there, the cap does not fire and the model runs unchanged. The proper fix
is for the closure to take `x` as an argument, which is a change to slabx.

`sigma_z`
---------
Pasquill-Gifford rural class D, the form already used for a passive plume:

    sigma_z = 0.06 x / sqrt(1 + 1.5e-3 x)

and the top-hat conversion is `k = 1.5`, the same factor slabx applies to the
width. **Neither is fitted and neither is adjustable.**
"""

from __future__ import annotations

import contextlib
import dataclasses
import inspect
import math
import threading
from typing import Any

import slabx.core.plume as _plume
import slabx.submodels.entrainment as _ent

__all__ = ["TOP_HAT_FACTOR", "sigma_z", "virtual_origin", "cap_depth",
           "depth_cap", "enable", "disable", "is_enabled", "fired_count",
           "reset_counts"]

#: Depth-to-sigma_z ratio. **Measured, not asserted.** SLAB's own passive
#: limit converges to 1.09: running a passive release and comparing the depth
#: against the Briggs curve gives 1.87 at 10 m, 1.20 at 100 m and 1.09 from
#: 300 m out. An earlier version asserted the textbook 1.5, which is above
#: what the model produces for a passive plume, so the ceiling sat where the
#: model never goes.
TOP_HAT_FACTOR = 1.09
#: Briggs open-country sigma_z, all six Pasquill classes:
#:     A, B, C, D   sigma_z = a x (1 + b x)^-1/2      (b = 0 for B)
#:     E, F         sigma_z = a x (1 + b x)^-1
#: Published coefficients, nothing fitted.
_SIGMA_Z = {
    "A": (0.20, 0.0, -0.5), "B": (0.12, 0.0, -0.5),
    "C": (0.08, 2.0e-4, -0.5), "D": (0.06, 1.5e-3, -0.5),
    "E": (0.03, 3.0e-4, -1.0), "F": (0.016, 3.0e-4, -1.0),
}
_A, _B = _SIGMA_Z["D"][0], _SIGMA_Z["D"][1]

_SQRT3 = math.sqrt(3.0)
_ORIGINAL = _ent.entrainment

#: How many times the cap has actually altered a result since `reset_counts`.
#: **This exists because a control once passed while the code did nothing.**
#: The frame walk was broken, the cap never fired, every case came back
#: unchanged, and NC1 and NC2 were recorded as passes. A negative control has
#: to be shown to have exercised the change; `fired_count` is how.
_counts = {"calls": 0, "ceiling": 0, "floor": 0}
#: The virtual origin for the run in progress, set on the first call from the
#: cloud's own depth. Reset by the context manager.
_origin = {"x_v": None}
_TARGETS = (_plume,)
_lock = threading.RLock()


def sigma_z(x: float, stability: str = "D") -> float:
    """
    Vertical dispersion coefficient [m], Briggs open country.

    **All six classes.** An earlier version provided only D on the grounds
    that the LH2 trials are all D. That was wrong: the dense-gas negative
    controls include class C and E releases, and applying the D curve to them
    put the ceiling in the wrong place and failed the control for a reason
    that had nothing to do with the hypothesis under test.
    """
    if x <= 0.0:
        return 0.0
    a, b, p = _SIGMA_Z.get(str(stability).upper()[:1], _SIGMA_Z["D"])
    return a * x * (1.0 + b * x) ** p


def virtual_origin(h0: float, stability: str = "D", *,
                   k: float = TOP_HAT_FACTOR) -> float:
    """
    The upwind distance `x_v` at which a passive layer would have depth `h0`.

    **The ceiling has to start from the cloud's own depth, not from zero.**
    `sigma_z(x)` is 0.09 m at one metre, so a pool source metres deep is
    crushed in its first step by a ceiling measured from the source. That is
    what rejected the first two registrations.

    Solving `k sigma_z(x_v) = h0` for the Pasquill-Gifford form

        sigma_z = A x / sqrt(1 + B x)

    gives a quadratic in `x_v`. `x_v` is a consequence of `h0`, not a fitted
    quantity: a source already deeper than any passive layer gets an `x_v`
    large enough that the ceiling never binds.
    """
    if h0 <= 0.0 or k <= 0.0:
        return 0.0
    t = h0 / k                         # required sigma_z
    # solved numerically, because the E and F forms are not quadratic
    lo, hi = 0.0, 1.0
    for _ in range(200):
        if sigma_z(hi, stability) >= t:
            break
        hi *= 2.0
    else:
        return hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if sigma_z(mid, stability) < t:
            lo = mid
        else:
            hi = mid
    x_v = 0.5 * (lo + hi)
    return x_v if math.isfinite(x_v) and x_v > 0.0 else 0.0


def cap_depth(h: float, x: float, stability: str = "D", *,
              k: float = TOP_HAT_FACTOR, x_v: float = 0.0) -> float:
    """The depth a passively-dispersing layer can reach at `x + x_v` [m]."""
    ceiling = k * sigma_z(x + x_v, stability)
    return h if ceiling <= 0.0 else min(h, ceiling)


#: Locals that carry the downwind position, in the order they are preferred.
#: `x` is `_build_stage`'s keyword argument and is the position of the stage
#: being built; `st.x` is the integrator state, used where the first is absent.
_X_LOCALS = ("x", "x_c")


def _caller_x() -> float | None:
    """
    The integrator's position, read from the calling frame.

    **Fails closed.** Any frame that does not carry a finite position returns
    `None` and the cap does not fire, so a change to slabx's internals
    disables this module rather than corrupting it.
    """
    frame = inspect.currentframe()
    try:
        for _ in range(5):
            frame = frame.f_back if frame is not None else None
            if frame is None:
                return None
            loc = frame.f_locals
            for name in _X_LOCALS:
                v = loc.get(name)
                if isinstance(v, (int, float)) and math.isfinite(v) and v > 0:
                    return float(v)
            st = loc.get("st")
            v = getattr(st, "x", None)
            if isinstance(v, (int, float)) and math.isfinite(v) and v > 0:
                return float(v)
        return None
    finally:
        del frame


#: The function this patch was installed on top of. **Both this module and
#: `plume_width` rebind `plume.entrainment`, so whichever is installed second
#: must call the first rather than the import-time original.** Installing one
#: over the other used to disable it silently: no error, no warning, and the
#: combined run was identical to the second module alone.
_base = {"fn": None}


def _chain_base():
    return _base["fn"] or _ORIGINAL


def _patched(cl, atm, fr, *args, coeffs=None, **kwargs) -> Any:
    """
    Two regimes, a ceiling and a floor.

    **Grounded** -- ambient turbulence sets the depth, and it cannot exceed
    what a passively dispersing layer reaches at the same distance.

    **Lofted** -- the plume's own entrainment sets it, and the depth grows
    with the rise: `dh/dx >= 2 beta w_c / u`, which is the Morton-Taylor-
    Turner `b = beta z` that Briggs's two-thirds law rests on.

    Applying only the first is what the earlier registration did, and it
    turned the cloud into a thin climbing ribbon.
    """
    _counts["calls"] += 1
    base = _chain_base()
    if coeffs is None:
        out = base(cl, atm, fr, *args, **kwargs)
    else:
        out = base(cl, atm, fr, *args, coeffs=coeffs, **kwargs)

    if getattr(cl, "is_lofted", False) and cl.w_c > 0.0 and cl.u > 0.0:
        beta = getattr(coeffs, "briggs_beta0", None) if coeffs else None
        if beta is None:
            from slabx.coefficients import COEFFS as _C
            beta = _C.briggs_beta0
        # `w` here is the reduced entrainment velocity; W_e = sqrt(3) w, and
        # dh/dx = W_e / u. The plume closure wants dh/dx = 2 beta w_c / u, so
        # the floor on `w` is 2 beta w_c / sqrt(3).
        floor = 2.0 * beta * cl.w_c / _SQRT3
        if math.isfinite(floor) and floor > out.w:
            try:
                _counts["floor"] += 1
                return dataclasses.replace(out, w=floor)
            except Exception:                           # noqa: BLE001
                return out
        return out

    x = _caller_x()
    if x is None or x <= 0.0:
        return out
    stab = getattr(atm, "stability", "D")
    if _origin["x_v"] is None:
        # Place the origin so that the ceiling equals the cloud's depth here.
        # **Wait for a finite depth**: the trajectory opens with h = 0 at a
        # negative x, and an origin placed from that lands half a metre
        # upwind and clips the source.
        if cl.h <= 0.0:
            return out
        _origin["x_v"] = max(0.0, virtual_origin(cl.h, stab) - x)
    if cl.h <= TOP_HAT_FACTOR * sigma_z(x + _origin["x_v"], stab):
        return out
    try:
        _counts["ceiling"] += 1
        return dataclasses.replace(out, w=min(out.w, 0.0))
    except Exception:                                   # noqa: BLE001
        return out


def fired_count() -> dict[str, int]:
    """
    How often the cap has changed a result.

    Check it after a negative control. **A control that passes with
    `ceiling` and `floor` both zero has not tested anything.**
    """
    return dict(_counts)


def reset_counts() -> None:
    for k in _counts:
        _counts[k] = 0


def is_enabled() -> bool:
    return _plume.entrainment is _patched


def enable() -> None:
    """Install the cap. Prefer `depth_cap()`."""
    with _lock:
        if _plume.entrainment is not _patched:
            _base["fn"] = _plume.entrainment
        _plume.entrainment = _patched


def disable() -> None:
    with _lock:
        _plume.entrainment = _base["fn"] or _ORIGINAL
        _base["fn"] = None


@contextlib.contextmanager
def depth_cap(active: bool = True):
    """
    Context manager, because the patch rebinds a module-level name and a bare
    `enable()` followed by an exception leaves it installed for the rest of
    the process.
    """
    with _lock:
        previous = _plume.entrainment
        prev_base = _base["fn"]
        _origin["x_v"] = None
        if active:
            # chain onto whatever is already installed, so that turning this
            # on does not turn `plume_width` off
            if previous is not _patched:
                _base["fn"] = previous
            _plume.entrainment = _patched
        else:
            _plume.entrainment = _ORIGINAL
    try:
        yield
    finally:
        with _lock:
            _plume.entrainment = previous
            _base["fn"] = prev_base
            _origin["x_v"] = None
