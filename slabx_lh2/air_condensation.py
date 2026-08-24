"""
Where nitrogen and oxygen leave the gas phase, and why it does not matter.

SLAB's EQ 40-41 treat dry air as a permanent gas. ADREA-HF condenses and
freezes nitrogen and oxygen, and PRESLHY D3.1 states that a liquid hydrogen
pool "will always be a multi-component pool containing liquid hydrogen and
solid humid air, i.e. at least solid oxygen, nitrogen and water", where an LNG
pool contains only solid water.

So the omission is real. This module measures what it costs, so that the
decision not to model it is a measurement rather than an assumption.

The answer is that **air condensation begins above the upper flammability
limit**. Onset is between 88 and 94 mol% hydrogen; the UFL is 75 mol%. Inside
the flammable range no nitrogen or oxygen has left the gas phase, so nothing
that a dispersion or separation-distance calculation reads is affected.

Where it does happen, it makes the cloud **lighter**, not heavier: the latent
heat raises the temperature and the heavy species leave the gas phase, and
both push the density down.

Saturation comes from CoolProp above each triple point and from
Clausius-Clapeyron anchored at the triple point with the enthalpy of
sublimation below it -- the same construction as `water_ice`, since CoolProp
clamps nitrogen at 63.15 K and oxygen at 54.36 K for the same reason it clamps
water. **No free parameters.**
"""

from __future__ import annotations

import math
from typing import Any

import CoolProp.CoolProp as CP

__all__ = ["SPECIES", "p_saturation", "adiabatic_mix", "condensation_onset",
           "UFL_HYDROGEN"]

_R = 8.314462
#: Upper flammability limit of hydrogen in air [mol %].
UFL_HYDROGEN = 75.0

#:  name -> (fluid, M [kg/mol], T_triple [K], dh_vap, dh_fus, cp_vap, cp_cond)
SPECIES: dict[str, tuple] = {
    "N2": ("Nitrogen", 0.028014, 63.151, 199e3, 25.7e3, 1040.0, 1600.0),
    "O2": ("Oxygen", 0.031999, 54.361, 213e3, 13.9e3, 918.0, 1500.0),
    "H2O": ("Water", 0.018015, 273.16, 2501e3, 333.4e3, 1860.0, 2050.0),
}
_CP_H2 = 10400.0
_CRIT: dict[str, float] = {}


def _critical(fluid: str) -> float:
    if fluid not in _CRIT:
        _CRIT[fluid] = float(CP.PropsSI("Tcrit", fluid))
    return _CRIT[fluid]

_M_H2 = 0.002016
_M_AR, _CP_AR = 0.039948, 520.0


def p_saturation(name: str, T: float) -> float:
    """
    Saturation (or sublimation) pressure [Pa] of a condensable species.

    Above the critical temperature there is no saturation line and the species
    cannot leave the gas phase at any partial pressure. `math.inf` is returned
    so that callers comparing a partial pressure against it condense nothing,
    which is the physical answer -- nitrogen is supercritical above 126.2 K and
    oxygen above 154.6 K, and both are reached in a diluted hydrogen cloud.
    """
    if name not in SPECIES:
        raise ValueError(f"unknown species {name!r}; have {sorted(SPECIES)}")
    fluid, M, Tt, dhv, dhf, _, _ = SPECIES[name]
    if T <= 0.0 or not math.isfinite(T):
        raise ValueError(f"temperature must be finite and > 0, got {T!r}")
    if T >= _critical(fluid):
        return math.inf
    if T >= Tt:
        return float(CP.PropsSI("P", "T", T, "Q", 0, fluid))
    p_t = float(CP.PropsSI("P", "T", Tt, "Q", 0, fluid))
    x = -(dhv + dhf) * M / _R * (1.0 / T - 1.0 / Tt)
    return 0.0 if x < -700.0 else p_t * math.exp(x)


def adiabatic_mix(w_h2: float, *, T_ambient: float = 288.15,
                  rh: float = 60.0, p: float = 101325.0,
                  allow_air: bool = True) -> dict[str, Any]:
    """
    Adiabatic mix of saturated hydrogen vapour with humid air.

    `w_h2` is the hydrogen mass fraction. With `allow_air=False` nitrogen and
    oxygen are held as permanent gases, which is what SLAB does; the pair of
    runs is the comparison.

    Returns ``{T, rho, rho_ratio, condensed, y_h2}``.
    """
    if not 0.0 < w_h2 < 1.0:
        raise ValueError(f"w_h2 must be in (0, 1), got {w_h2!r}")
    if not 0.0 <= rh <= 100.0:
        raise ValueError(f"rh must be in [0, 100], got {rh!r}")

    p_w = rh / 100.0 * float(CP.PropsSI("P", "T", T_ambient, "Q", 0, "Water"))
    y_w = p_w / p
    y = {"H2O": y_w, "N2": (1 - y_w) * 0.7808, "O2": (1 - y_w) * 0.2095}
    y_ar = (1 - y_w) * 0.0097
    M_air = y_ar * _M_AR + sum(y[k] * SPECIES[k][1] for k in y)

    w_air = 1.0 - w_h2
    m = {k: w_air * y[k] * SPECIES[k][1] / M_air for k in y}
    m_ar = w_air * y_ar * _M_AR / M_air
    n_tot = w_h2 / _M_H2 + m_ar / _M_AR + sum(m[k] / SPECIES[k][1] for k in m)

    H = (w_h2 * _CP_H2 * 20.37 + m_ar * _CP_AR * T_ambient
         + sum(m[k] * SPECIES[k][5] * T_ambient for k in m))

    def enthalpy(T: float):
        h = w_h2 * _CP_H2 * T + m_ar * _CP_AR * T
        cond = {}
        for k, mk in m.items():
            _, M, Tt, dhv, dhf, cpv, cpc = SPECIES[k]
            if not allow_air and k != "H2O":
                h += mk * cpv * T
                cond[k] = 0.0
                continue
            ps = p_saturation(k, T)
            n_max = n_tot if math.isinf(ps) else min(ps / p, 1.0) * n_tot
            n_v = min(mk / M, max(n_max, 0.0))
            mv, mc = n_v * M, mk - n_v * M
            h += mv * cpv * T + mc * (cpc * T - (dhv + (dhf if T < Tt else 0.0)))
            cond[k] = mc
        return h, cond

    lo, hi = 15.0, T_ambient
    for _ in range(200):
        T = 0.5 * (lo + hi)
        if enthalpy(T)[0] < H:
            lo = T
        else:
            hi = T
    T = 0.5 * (lo + hi)
    cond = enthalpy(T)[1]

    n_gas = w_h2 / _M_H2 + m_ar / _M_AR
    m_gas = w_h2 + m_ar
    for k, mk in m.items():
        n_gas += (mk - cond[k]) / SPECIES[k][1]
        m_gas += mk - cond[k]
    rho_gas = p * (m_gas / n_gas) / (_R * T)
    rho = (m_gas + sum(cond.values())) / (m_gas / rho_gas)
    rho_a = p * 0.028718 / (_R * T_ambient)
    return {"T": T, "rho": rho, "rho_ratio": rho / rho_a,
            "condensed": cond, "y_h2": (w_h2 / _M_H2) / n_tot * 100.0}


def condensation_onset(*, T_ambient: float = 288.15, rh: float = 60.0,
                       species: str = "N2", tol: float = 1e-4
                       ) -> dict[str, Any]:
    """
    Hydrogen mole fraction [mol %] at which `species` begins to condense.

    Bisected on the mass fraction. Returns the onset alongside the upper
    flammability limit, because the point of the calculation is the comparison:
    ``inside_flammable_range`` is False whenever onset sits above the UFL.
    """
    def condenses(w: float) -> bool:
        return adiabatic_mix(w, T_ambient=T_ambient, rh=rh,
                             allow_air=True)["condensed"][species] > 0.0

    lo, hi = 0.01, 0.99
    if not condenses(hi):
        return {"species": species, "onset_mol_pct": None,
                "ufl_mol_pct": UFL_HYDROGEN, "inside_flammable_range": False,
                "note": "no condensation at any composition"}
    if condenses(lo):
        onset_w = lo
    else:
        while hi - lo > tol:
            mid = 0.5 * (lo + hi)
            if condenses(mid):
                hi = mid
            else:
                lo = mid
        onset_w = hi
    onset = adiabatic_mix(onset_w, T_ambient=T_ambient, rh=rh)
    return {"species": species, "onset_mol_pct": onset["y_h2"],
            "onset_mass_fraction": onset_w, "onset_T_K": onset["T"],
            "ufl_mol_pct": UFL_HYDROGEN,
            "inside_flammable_range": onset["y_h2"] <= UFL_HYDROGEN}
