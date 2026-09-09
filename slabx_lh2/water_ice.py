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
curve the error is a factor of 3.2 at 260 K, 23 at 240 K and **3900** at
200 K.

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
           "correction_state", "clamped", "ClampedWater", "p_sublimation",
           "SublimationWater", "with_sublimation"]

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

    def __init__(self, inner: Any, p_ambient: float = 101325.0, *,
                 correct_pressure: bool = True,
                 correct_fusion: bool = True) -> None:
        if p_ambient <= 0.0:
            raise ValueError(f"p_ambient must be > 0, got {p_ambient!r}")
        self._inner = inner
        self._p_ambient = float(p_ambient)
        self._correct_pressure = bool(correct_pressure)
        self._correct_fusion = bool(correct_fusion)

    # -- the three overridden quantities ------------------------------------
    def saturation_ratio(self, T: float) -> float:
        if T >= T_TRIPLE or not self._correct_pressure:
            return self._inner.saturation_ratio(T)
        return p_sublimation(T) / self._p_ambient

    def d_saturation_ratio(self, T: float) -> float:
        if T >= T_TRIPLE or not self._correct_pressure:
            return self._inner.d_saturation_ratio(T)
        h = max(1e-3 * abs(T), 1e-3)
        lo = max(T - h, 1e-6)
        hi = min(T + h, T_TRIPLE)
        if hi <= lo:
            return 0.0
        return (self.saturation_ratio(hi) - self.saturation_ratio(lo)) / (hi - lo)

    def dh_vap(self, T: float) -> float:
        base = self._inner.dh_vap(T)
        return (base + DH_FUSION
                if self._correct_fusion and T < T_TRIPLE else base)

    # -- everything else is the wrapped backend -----------------------------
    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def __repr__(self) -> str:
        return f"SublimationWater({self._inner!r})"

    @property
    def inner(self) -> Any:
        """The backend this wraps, for comparison runs."""
        return self._inner


class ClampedWater:
    """
    A water backend that holds saturation flat below the triple point.

    **This reproduces the defect on purpose.** It exists so that the 2x2
    ablation can run against any version of slabx: 1.0.6 corrected the clamp
    upstream, so `coolprop_water()` no longer gives a "correction off" arm and
    the ablation silently collapses -- every cell returns the corrected
    answer and the design looks like it shows the correction does nothing.

    Do not use it for anything but that comparison.
    """

    _slab_lh2_clamped = True

    def __init__(self, inner: Any, T_triple: float = T_TRIPLE) -> None:
        self._inner = inner
        self._T = float(T_triple)

    def saturation_ratio(self, T: float) -> float:
        return self._inner.saturation_ratio(max(T, self._T))

    def d_saturation_ratio(self, T: float) -> float:
        return (0.0 if T < self._T
                else self._inner.d_saturation_ratio(T))

    def dh_vap(self, T: float) -> float:
        return self._inner.dh_vap(max(T, self._T))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def __repr__(self) -> str:
        return f"ClampedWater({self._inner!r})"


def clamped(backend: Any):
    """
    The backend as it behaved before the correction, whatever version it is.

    Use this as the "off" arm of an ablation so that the comparison means the
    same thing on slabx 1.0.4 and 1.0.6.
    """
    if getattr(backend, "_slab_lh2_clamped", False):
        return backend
    if getattr(backend, "_slabx_lh2_sublimation", False):
        backend = backend.inner
    return ClampedWater(backend)


def correction_state(backend: Any, *, pressure_tol: float = 0.05,
                     fusion_tol: float = 0.10) -> tuple[bool, bool]:
    """
    Return ``(pressure_corrected, fusion_corrected)`` for a water backend.

    The two checks must be independent. slabx 1.0.5 corrected the saturation
    pressure, while 1.0.6 added the fusion enthalpy. Treating a corrected
    pressure curve as proof that both changes are present silently omits
    333.4 kJ/kg on 1.0.5.

    Pressure is checked against the *shape* of the IAPWS curve, normalised at
    the triple point so that the ambient pressure cancels. Fusion is checked
    from the enthalpy jump across the triple point. The latter is insensitive
    to the ordinary temperature dependence of latent heat.
    """
    if getattr(backend, "_slabx_lh2_sublimation", False):
        pressure = (getattr(backend, "_correct_pressure", False)
                    or correction_state(backend.inner,
                                        pressure_tol=pressure_tol,
                                        fusion_tol=fusion_tol)[0])
        fusion = (getattr(backend, "_correct_fusion", False)
                  or correction_state(backend.inner,
                                      pressure_tol=pressure_tol,
                                      fusion_tol=fusion_tol)[1])
        return bool(pressure), bool(fusion)

    try:
        near = backend.saturation_ratio(T_TRIPLE - 1e-3)
        cold = backend.saturation_ratio(200.0)
    except Exception:                              # noqa: BLE001
        pressure = False
    else:
        target = p_sublimation(200.0) / p_sublimation(T_TRIPLE - 1e-3)
        pressure = (near > 0.0 and math.isclose(
            cold / near, target, rel_tol=pressure_tol, abs_tol=0.0))

    eps = 1e-3
    try:
        below = backend.dh_vap(T_TRIPLE - eps)
        above = backend.dh_vap(T_TRIPLE + eps)
        jump = below - above
    except Exception:                              # noqa: BLE001
        fusion = False
    else:
        fusion = math.isclose(jump, DH_FUSION, rel_tol=fusion_tol,
                              abs_tol=10_000.0)
    return bool(pressure), bool(fusion)


def already_corrected(backend: Any, *, tol: float = 0.05) -> bool:
    """Whether both the IAPWS pressure and fusion enthalpy are present."""
    pressure, fusion = correction_state(backend, pressure_tol=tol)
    return pressure and fusion


def with_sublimation(backend: Any, p_ambient: float = 101325.0):
    """
    Wrap a water backend so that its saturation follows the sublimation curve
    below the triple point.

    Does not modify `backend`. Returns it unchanged when it already carries
    the correction -- from a previous call, or **from slabx 1.0.6 or later,
    which has it upstream**. Either way the enthalpy of fusion cannot be
    added twice.

    Against 1.0.6 and later this is a no-op and can be dropped from calling
    code; it is kept so that the same script runs against 1.0.4 and the
    pressure-only 1.0.5 backend.
    """
    if getattr(backend, "_slabx_lh2_sublimation", False):
        return backend
    pressure, fusion = correction_state(backend)
    if pressure and fusion:
        return backend
    return SublimationWater(backend, p_ambient=p_ambient,
                            correct_pressure=not pressure,
                            correct_fusion=not fusion)
