"""
Water saturation below the triple point.

The defect
----------
`slabx.thermo.coolprop.CoolPropThermo` clamps the temperature to the fluid's
triple point before every saturation query.  Its docstring says why: the
equilibrium solver brackets its root over a wide interval and evaluates
unphysical temperatures on the way, and those evaluations only need to be
finite and monotone.

That is sound for the released substance -- hydrogen's triple point is 13.96 K
and methane's is 90.7 K, both below anything a cloud of them reaches.

**Water's triple point is 273.16 K, and every cryogenic cloud is below it.**
For water the clamp is not a numerical guard, it is the model: it returns the
0 C saturation ratio at any temperature, which says a cloud at 200 K holds as
much water vapour as air at freezing.  Measured against the IAPWS sublimation
curve the error is a factor of 3 at 260 K, 24 at 240 K and 4136 at 200 K.

The fix
-------
Below the triple point the phase in equilibrium with vapour is ice, and the
reference correlation is the IAPWS sublimation pressure of Wagner, Riethmann,
Feistel & Harvey (2011):

    ln(p / p_t) = (a1 th^b1 + a2 th^b2 + a3 th^b3) / th,     th = T / T_t

with T_t = 273.16 K and p_t = 611.657 Pa.  The latent heat is raised by the
enthalpy of fusion, because the transition is vapour to solid rather than
vapour to liquid.  **No free parameters.**

Usage
-----
    from slabx_lh2.water_ice import with_sublimation
    from slabx.thermo.coolprop import coolprop_water

    water = with_sublimation(coolprop_water())

`with_sublimation` returns a wrapper and does not modify the backend it is
given, so the same backend can be used patched and unpatched in one process --
which is what the negative controls need.  Applying it twice is a no-op rather
than adding the heat of fusion twice.
"""

from __future__ import annotations

import math
from typing import Any

__all__ = ["T_TRIPLE", "P_TRIPLE", "DH_FUSION", "already_corrected",
           "p_sublimation", "SublimationWater", "with_sublimation"]

#: Triple point of water [K] (IAPWS).
T_TRIPLE = 273.16
#: Triple point pressure of water [Pa] (IAPWS).
P_TRIPLE = 611.657
#: Enthalpy of fusion of water at the triple point [J/kg].
DH_FUSION = 333400.0

_A = (-0.212144006e2, 0.273203819e2, -0.610598130e1)
_B = (0.333333333e-2, 0.120666667e1, 0.170333333e1)

#: Below this the IAPWS correlation underflows to zero in double precision.
_T_FLOOR = 5.0


def p_sublimation(T: float) -> float:
    """
    IAPWS sublimation pressure of ice Ih [Pa].

    Defined for ``0 < T <= T_TRIPLE``.  Above the triple point ice and vapour
    are not in equilibrium and the correlation is not valid there -- it does
    not diverge, it quietly returns a wrong number, so this raises instead.

    Below about 5 K the result underflows to zero in double precision; zero is
    returned, which is correct to every digit that matters.
    """
    if not math.isfinite(T):
        raise ValueError(f"temperature must be finite, got {T!r}")
    if T > T_TRIPLE:
        raise ValueError(
            f"the sublimation curve is defined up to the triple point "
            f"{T_TRIPLE} K; got {T} K. Use the liquid saturation curve above it."
        )
    if T <= _T_FLOOR:
        return 0.0
    th = T / T_TRIPLE
    s = sum(a * th ** b for a, b in zip(_A, _B))
    x = s / th
    if x < -700.0:                       # exp underflow guard
        return 0.0
    return P_TRIPLE * math.exp(x)


class SublimationWater:
    """
    A water backend whose saturation follows the IAPWS sublimation curve below
    the triple point.

    Everything other than ``saturation_ratio``, ``d_saturation_ratio`` and
    ``dh_vap`` is delegated to the wrapped backend unchanged.
    """

    #: marker so that `with_sublimation` is idempotent
    _slabx_lh2_sublimation = True

    def __init__(self, inner: Any, p_ambient: float = 101325.0) -> None:
        if p_ambient <= 0.0:
            raise ValueError(f"p_ambient must be > 0, got {p_ambient!r}")
        self._inner = inner
        self._p_ambient = float(p_ambient)

    # -- the three overridden quantities ------------------------------------
    def saturation_ratio(self, T: float) -> float:
        if T >= T_TRIPLE:
            return self._inner.saturation_ratio(T)
        return p_sublimation(T) / self._p_ambient

    def d_saturation_ratio(self, T: float) -> float:
        if T >= T_TRIPLE:
            return self._inner.d_saturation_ratio(T)
        h = max(1e-3 * abs(T), 1e-3)
        lo = max(T - h, 1e-6)
        hi = min(T + h, T_TRIPLE)
        if hi <= lo:
            return 0.0
        return (self.saturation_ratio(hi) - self.saturation_ratio(lo)) / (hi - lo)

    def dh_vap(self, T: float) -> float:
        base = self._inner.dh_vap(T)
        return base + DH_FUSION if T < T_TRIPLE else base

    # -- everything else is the wrapped backend -----------------------------
    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def __repr__(self) -> str:
        return f"SublimationWater({self._inner!r})"

    @property
    def inner(self) -> Any:
        """The backend this wraps, for comparison runs."""
        return self._inner


def already_corrected(backend: Any, *, tol: float = 0.05) -> bool:
    """
    Whether `backend` already follows the sublimation curve below the triple
    point.

    **slabx 1.0.6 carries this correction upstream**, so wrapping one of its
    backends would add the enthalpy of fusion a second time -- 12 % on
    `dh_vap`, and silently, because the saturation ratio comes out identical
    either way. The check is behavioural rather than a version comparison: it
    asks the backend what it returns at 200 K and compares against the flat
    triple-point value the clamp would give.

    **This detects "not clamped", which is not the same as "follows IAPWS".**
    The legacy Antoine backend extrapolates its liquid curve below the triple
    point rather than holding flat, so it passes -- and it is 2.35 times the
    sublimation pressure at 200 K. Wrapping it would be wrong for a different
    reason (its `dh_vap` is the liquid value, so the wrapper's addition of the
    fusion enthalpy would be the correct move while the pressure stayed on the
    liquid line), and leaving it alone keeps the two consistent with each
    other. The legacy backend is a reference implementation, not the one to
    use for a cryogenic release; `CoolPropThermo` is.
    """
    try:
        flat = backend.saturation_ratio(T_TRIPLE - 1e-6)
        cold = backend.saturation_ratio(200.0)
    except Exception:                              # noqa: BLE001
        return False
    if flat <= 0.0:
        return False
    return cold / flat < 1.0 - tol


def with_sublimation(backend: Any, p_ambient: float = 101325.0):
    """
    Wrap a water backend so that its saturation follows the sublimation curve
    below the triple point.

    Does not modify `backend`. Returns it unchanged when it already carries
    the correction -- from a previous call, or **from slabx 1.0.6 or later,
    which has it upstream**. Either way the enthalpy of fusion cannot be
    added twice.

    Against 1.0.6 and later this is a no-op and can be dropped from calling
    code; it is kept so that the same script runs against 1.0.4.
    """
    if getattr(backend, "_slab_lh2_sublimation", False):
        return backend
    if already_corrected(backend):
        return backend
    return SublimationWater(backend, p_ambient=p_ambient)
