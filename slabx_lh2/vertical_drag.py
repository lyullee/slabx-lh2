"""
Pressure drag on a rising plume. **Exploratory.**

Status
------
**This is not an adopted module.** It is carried so that a second, independent
mechanism against the over-rise can be compared with the first, and it should
appear in a paper as an exploratory comparison or in supplementary material --
never as part of the model that produced a result.

Against the band `PREREG_lh2_plume_width` fixed for the rise exponent, both
corrections together reach 0.86 to 1.30 on the four NASA trials, against a
required 0.6 to 0.9: **one of four**. The width coupling alone reaches
1.05 to 1.28. Both are partial and neither is validated.

Pressure drag on a rising plume.

The problem
-----------
`slabx_lh2.plume_width` recovers part of the bent-over rise law and not all of
it. `slabx_lh2.diagnostics.rise_scaling` locates the shortfall: the exponent is
`2/(s+1)` with `s = dlnB/dlnz + dlnh/dlnz`, Briggs needs `s = 2`, and the model
with the coupling reaches 0.62 to 1.01 -- the depth is not coupled to the rise
at all and the width only partway.

Mack & Boot's extension of EFFECTS (*J. Loss Prev. Process Ind.*, 2023) reports
the same symptom in a different code -- "for strongly buoyant plumes, it was
observed that vertical plume speeds are overpredicted by some integral models"
and "only during the rising phase of strongly buoyant plumes buoyancy was
initially over predicted resulting in too high plume trajectories" -- and takes
a different route to it. Rather than the added-mass concept, which reduces the
buoyancy term, they add a drag force that depends on the vertical velocity and
the plume's shape:

    C_d  = C_d0 + C_d1 (1 - AR),          AR = h / B
    dF_z = C_d (rho_a / 2) cos^2(phi) w^2 B dx

`AR` is the aspect ratio normal to the plume axis and `phi` the trajectory
angle. For a continuous release **the coefficients are not fitted**: `C_d0` =
1.17 is the classical drag coefficient of a circular cylinder in crossflow, and
`C_d1` = 1.2 is the increase towards a flat plate taken from numerical results
over the aspect-ratio range. Mack & Boot state that only the coefficients for
the *instantaneous* release were adapted against experiment.

What this is and is not
-----------------------
This is a **different mechanism** from the width coupling, not a replacement.
The coupling gives the cloud the inertia a real plume grows; the drag opposes
the rise directly. Both address the same symptom and they are not alternatives
-- which of them dominates, and whether either is sufficient, is what
`PREREG_lh2_vertical_drag` was registered to find out.

The authors' own caveat is worth repeating: "this method is just an
approximation for non-solid objects like plumes. Coefficients might have to be
adapted due to the fact that plumes are gaseous objects with density variations
and therefore behave differently compared with solid objects in crossflow."

**The coefficients are not adapted here.** If the published values do not work
in this formulation, that is the result.

Usage
-----
    from slabx_lh2.vertical_drag import vertical_drag

    with vertical_drag():
        traj, used = run_dispersion(...)

Gated on the model's own lift-off switch and on a positive rise velocity, so a
grounded or sinking cloud is untouched.
"""

from __future__ import annotations

import contextlib
import dataclasses
import math
import threading

import slabx.core.plume as _plume
import slabx.submodels.entrainment as _ent



# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------
#
# These modules install themselves by rebinding a module-level name, which is
# process-global. Two threads cannot run the same model with the patch in
# different states, and no amount of locking fixes that -- the state being
# contended is a global, not a resource.
#
# slabx offers no seam for injecting the closure per run, so the patch is what
# is available. What can be done is to **fail loudly instead of silently**: a
# second thread entering the context while another holds it in a different
# state raises, rather than quietly getting the other thread's physics.
#
# For a service that has to answer concurrently -- a digital twin, a request
# handler -- run the model in a worker process, not a worker thread.

class ConcurrentPatchError(RuntimeError):
    """Raised when two threads want the same global patch in different states."""


class _PatchState:
    """Owner-thread and nesting bookkeeping for one module-global patch."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._lock = threading.RLock()
        self._owner: int | None = None
        self._depth = 0
        self._active: bool | None = None

    def acquire(self, active: bool) -> None:
        me = threading.get_ident()
        with self._lock:
            if self._owner is None:
                self._owner, self._depth, self._active = me, 1, active
                return
            if self._owner == me:
                if self._active != active:
                    self._active = active          # nested override, same thread
                self._depth += 1
                return
            raise ConcurrentPatchError(
                f"{self._name} is held by thread {self._owner} and thread {me} "
                f"wants it too. This patch is a module-global rebinding, so the "
                f"two threads cannot have different physics. Run the model in "
                f"separate processes.")

    def release(self) -> None:
        with self._lock:
            self._depth -= 1
            if self._depth <= 0:
                self._owner, self._depth, self._active = None, 0, None


__all__ = ["CD0_CONTINUOUS", "CD1_CONTINUOUS", "ConcurrentPatchError",
           "drag_coefficient", "drag_force", "enable", "disable",
           "is_enabled", "vertical_drag"]

#: Circular cylinder in crossflow, classical measurement.
CD0_CONTINUOUS = 1.17
#: Increase from cylinder (AR = 1) towards flat plate (AR -> 0).
CD1_CONTINUOUS = 1.2

#: `core.plume` does `from ..submodels.entrainment import fluxes`, so it holds
#: its own reference and patching the submodule alone does nothing. Both names
#: are swapped.
_ORIGINAL = _ent.fluxes
_TARGETS = (_ent, _plume)
_lock = threading.RLock()
_state = _PatchState("vertical_drag")


def drag_coefficient(aspect_ratio: float, cd0: float = CD0_CONTINUOUS,
                     cd1: float = CD1_CONTINUOUS) -> float:
    """
    ``C_d = cd0 + cd1 (1 - AR)``, with ``AR = h/B`` clipped to [0, 1].

    Above ``AR = 1`` the cloud is taller than it is wide and the crossflow
    analogy has run out; the coefficient is held at its cylinder value rather
    than allowed to fall below it.
    """
    if not math.isfinite(aspect_ratio) or aspect_ratio < 0.0:
        raise ValueError(
            f"aspect ratio must be finite and >= 0, got {aspect_ratio!r}")
    ar = min(aspect_ratio, 1.0)
    return cd0 + cd1 * (1.0 - ar)


def drag_force(cl, atm) -> float:
    """
    Vertical pressure-drag force per unit downwind length [N/m], negative.

    ``dF_z/dx = -C_d (rho_a/2) cos^2(phi) w^2 B``, with the trajectory angle
    taken from the velocity components, ``cos^2(phi) = 1/(1 + (w/u)^2)``.

    Returns 0 for a grounded or sinking cloud. EQ 37's own vertical friction
    already carries a ``c_drag_top |w| w`` term on the interface; this is the
    form drag on the plume as a bluff body, which that term does not
    represent.
    """
    w = cl.w_c
    if w <= 0.0 or cl.b_half <= 0.0 or cl.h <= 0.0:
        return 0.0
    rho_a = getattr(atm, "rho", 0.0)
    if rho_a <= 0.0:
        return 0.0
    u = max(getattr(cl, "u", 0.0), 1e-9)
    cos2 = 1.0 / (1.0 + (w / u) ** 2)
    width = 2.0 * cl.b_half                     # B is the full width
    cd = drag_coefficient(cl.h / width)
    f = cd * 0.5 * rho_a * cos2 * w * w * width
    return -f if math.isfinite(f) else 0.0


def _patched(cl, atm, fr, *args, **kwargs):
    out = _ORIGINAL(cl, atm, fr, *args, **kwargs)
    if not cl.is_lofted or cl.w_c <= 0.0:
        return out
    f = drag_force(cl, atm)
    if f >= 0.0:
        return out
    scale = cl.b_half_x if getattr(cl, "is_puff", False) else 1.0
    return dataclasses.replace(out, f_w=out.f_w + f * scale)


def _install(fn) -> None:
    for mod in _TARGETS:
        setattr(mod, "fluxes", fn)


def is_enabled() -> bool:
    return all(getattr(m, "fluxes") is _patched for m in _TARGETS)


def enable() -> None:
    with _lock:
        _install(_patched)


def disable() -> None:
    with _lock:
        _install(_ORIGINAL)


@contextlib.contextmanager
def vertical_drag(active: bool = True):
    """Install the drag for the duration of the block, then restore."""
    _state.acquire(active)
    try:
        with _lock:
            previous = [getattr(m, "fluxes") for m in _TARGETS]
            _install(_patched if active else _ORIGINAL)
        try:
            yield
        finally:
            with _lock:
                for mod, fn in zip(_TARGETS, previous):
                    setattr(mod, "fluxes", fn)
    finally:
        _state.release()
