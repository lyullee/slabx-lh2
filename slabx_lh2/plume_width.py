"""
Coupling the cloud width to its rise.

The defect
----------
A bent-over buoyant plume limits its own rise because entrainment across its
perimeter makes the width follow the height: ``b ~ beta z``, so
``R ~ rho u beta^2 z^2`` and ``dz/dx = Gw/(R u)`` gives ``z ~ x^(2/3)``.

SLAB has no such coupling.  Once the cloud lofts, EQ 7 keeps setting the width
from gravity spreading and ground-level ambient entrainment, and the cloud
reaches hundreds of metres while staying six to nine times narrower than a
plume of its own height.  Measured on NASA White Sands Test 6: the fitted rise
exponent is 1.22 against Briggs's 0.67, and ``B/(beta z_c)`` is 0.107 at the
100 m arc.

The fix
-------
The width slope in EQ 7 is ``(sqrt3 (rho_a/rho) V_e + V_g)/u``, so requiring it
to gain ``beta w_c/u`` once the cloud is lofted means adding

    V_e  +=  beta w_c rho / (sqrt3 rho_a)

``V_e`` also enters EQ 2a, so the widening entrains.  That is the physical
content of the coupling, not a side effect.

``beta`` is ``COEFFS.briggs_beta0`` = 0.4, already in the coefficient table.
**No new coefficient.**

Measured effect: rise exponent 1.220 to 0.869, ``B/(beta z_c)`` 0.107 to 0.727,
NASA cloud top 5.0 to 2.2 times the observed 20 m.  Bit-identical on the ten
LNG pool trials, on Prairie Grass, and on the four FFI trials, none of which
lofts.

Usage
-----
    from slabx_lh2.plume_width import plume_width_coupling

    with plume_width_coupling():
        traj, used = run_dispersion(...)

The context manager restores the original on the way out, including on an
exception.  `enable()` and `disable()` are kept for interactive use but the
context manager is what scripts should use: a bare `enable()` followed by an
exception leaves the patch installed for the rest of the process.
"""

from __future__ import annotations

import contextlib
import dataclasses
import math
import threading

import slabx.core.plume as _plume
from slabx.coefficients import COEFFS



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


__all__ = ["ConcurrentPatchError", "enable", "disable", "is_enabled",
           "plume_width_coupling"]

_ORIGINAL = _plume.entrainment
_SQRT3 = math.sqrt(3.0)
_lock = threading.RLock()
_depth = 0
_state = _PatchState("plume_width_coupling")


def _patched(cl, atm, fr, *args, coeffs=COEFFS, **kwargs):
    out = _ORIGINAL(cl, atm, fr, *args, coeffs=coeffs, **kwargs)
    if not cl.is_lofted or cl.w_c <= 0.0:
        return out
    rho_a = getattr(atm, "rho", 0.0)
    if rho_a <= 0.0 or not math.isfinite(cl.rho) or cl.rho <= 0.0:
        return out
    beta = coeffs.briggs_beta0
    v_plume = beta * cl.w_c * cl.rho / (_SQRT3 * rho_a)
    if not math.isfinite(v_plume) or v_plume <= 0.0:
        return out
    return dataclasses.replace(out, v=out.v + v_plume)


def is_enabled() -> bool:
    return _plume.entrainment is _patched


def enable() -> None:
    """Install the coupling. Prefer `plume_width_coupling()`."""
    with _lock:
        _plume.entrainment = _patched


def disable() -> None:
    """Restore the original entrainment closure."""
    with _lock:
        _plume.entrainment = _ORIGINAL


@contextlib.contextmanager
def plume_width_coupling(active: bool = True):
    """
    Install the coupling for the duration of the block, then restore.

    Nests correctly and restores on an exception.  `active=False` runs the
    block with the coupling off, which is what an A/B comparison wants:

        for active in (False, True):
            with plume_width_coupling(active):
                ...
    """
    global _depth
    _state.acquire(active)
    try:
        with _lock:
            previous = _plume.entrainment
            _depth += 1
            _plume.entrainment = _patched if active else _ORIGINAL
        try:
            yield
        finally:
            with _lock:
                _depth -= 1
                _plume.entrainment = previous
    finally:
        _state.release()
