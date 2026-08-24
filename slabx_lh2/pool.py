"""
Equilibrium radius of a cryogenic pool.

SLAB's `EvaporatingPool` takes the pool area as an input.  For a downward
release onto flat ground the area is not free: the pool grows until what it
covers evaporates as fast as liquid arrives.  RR986 reports exactly that --
"once the pool was established the extent of the pool remained constant
throughout the release. This could be an equilibrium effect at this flow rate."

    pi R^2 E = q (1 - x)      =>      R = sqrt( q (1-x) / (pi E) )

`x` is the post-flash vapour fraction from an isenthalpic flash to atmospheric
pressure.  `E` is the evaporative mass flux, and it does not have to be
supplied: `submodels/ground.py` gives it.  Semi-infinite conduction into
concrete supplies 30.7 kW/m2 at 60 s under liquid hydrogen, and the observed
late-phase regression rate of about 1 mm/s requires 31.5 kW/m2 -- a ratio of
0.97.  The implied flux is 0.0690 kg/(m2 s) against 0.0708 from the literature
regression rate, a difference of 2.6 %.

`E` is a **choice, not a free parameter fitted here**, but it is not a single
number either: PRESLHY E3.4 measured the pool regression on concrete falling
from 0.90 to 0.54 mm/s over 200 to 740 s as the ground cooled. Taking the
literature 1 mm/s gives 0.67 m for E3.5 trial 7 against an observed 0.70;
taking E3.4's early measured value gives 0.70 m. **The calibration below is
quoted at 1 mm/s and is sensitive to that choice at the level of 30 %.**

Calibration against six reported pool radii gives a median predicted/observed
of 1.03 (1.11 including NASA, whose pool was confined):

    E3.5 trial 7    0.67 / 0.70 m
    E3.5 trial 13   0.95 / 1.20
    RR986 test 6    0.55 / 0.83
    FFI Test 1      0.95 / 0.75
    FFI Test 7      0.83 / 0.75
    FFI Test 3      1.35 / 0.75

NASA Test 6 is excluded: its pool was confined by the 9.1 m pond's 0.6 m clay
walls, and `max_radius` exists for that case.

Note what this module is **not**.  `PREREG_lh2_impinging` tested treating a
downward jet as a momentumless pool for dispersion and rejected it: the FFI
Test 4 / Test 3 ratio went to 13,684 against a measured 2.69.  The radius
calculation stands; using it as a dispersion source does not.
"""

from __future__ import annotations

import math
from typing import Any

import CoolProp.CoolProp as CP

__all__ = ["REGRESSION_RATE", "CRITICAL_HEAT_FLUX", "SUBSTRATES",
           "flux_from_regression", "vapour_fraction", "equilibrium_radius",
           "ground_limited_flux", "pool_radius"]

#: Critical heat flux for liquid hydrogen boiling on a flat horizontal plate
#: [W/m2], Shirai et al., *Cryogenics* 50 (2010) 410-416, as used by PRESLHY
#: E3.4. The semi-infinite conduction solution diverges as t -> 0 and this is
#: what actually limits it: above the CHF the surface goes into film boiling
#: and the heat transfer collapses rather than growing.
CRITICAL_HEAT_FLUX = 120e3

#: Regression rate of a liquid hydrogen pool [m/s], commonly quoted at about
#: 1 mm/s (Takeno 1994, Bailey 1960, ISO TR 15916:2015 Annex B.1).
#:
#: **PRESLHY E3.4 measured 0.54 to 0.90 mm/s** on concrete, falling with time
#: as the ground cools -- 0.90 at 200 s and 0.54 at 740 s. The single number
#: is a convenience; `ground_limited_flux` gives the time dependence, which is
#: what actually governs the pool.
REGRESSION_RATE = 1.0e-3
#: Range measured by PRESLHY E3.4 on concrete, Table 3.
REGRESSION_RATE_MEASURED = (0.54e-3, 0.90e-3)


def flux_from_regression(rho_liquid: float,
                         regression_rate: float = REGRESSION_RATE) -> float:
    """Evaporative mass flux [kg/(m2 s)] from a linear regression rate."""
    if rho_liquid <= 0.0:
        raise ValueError(f"rho_liquid must be > 0, got {rho_liquid!r}")
    if regression_rate <= 0.0:
        raise ValueError(
            f"regression_rate must be > 0, got {regression_rate!r}")
    return rho_liquid * regression_rate


def ground_limited_flux(substrate, dh_vap: float, T_ambient: float,
                        T_pool: float, elapsed: float, *,
                        critical_heat_flux: float | None = CRITICAL_HEAT_FLUX
                        ) -> float:
    """
    Evaporative mass flux [kg/(m2 s)] set by conduction into the ground.

    Semi-infinite solid drawn on at the surface: ``q = k dT / sqrt(pi alpha t)``.
    Under liquid hydrogen this is the limiting resistance, unlike LNG where the
    convective film limits for the first few minutes.

    **Capped at the critical heat flux.** The conduction solution diverges as
    ``t -> 0``, which PRESLHY E3.4 calls out as unphysical: nucleate boiling
    holds only up to the CHF, and above it the surface goes into film boiling
    and the transfer collapses. For LH2 on concrete at 262 K of superheat the
    cap binds for the first 24 s. Pass `critical_heat_flux=None` to see the
    uncapped solution.
    """
    if elapsed <= 0.0:
        raise ValueError(f"elapsed must be > 0, got {elapsed!r}")
    if dh_vap <= 0.0:
        raise ValueError(f"dh_vap must be > 0, got {dh_vap!r}")
    if critical_heat_flux is not None and critical_heat_flux <= 0.0:
        raise ValueError(
            f"critical_heat_flux must be > 0 or None, "
            f"got {critical_heat_flux!r}")
    dT = T_ambient - T_pool
    if dT <= 0.0:
        return 0.0
    q = substrate.conductivity * dT / math.sqrt(
        math.pi * substrate.diffusivity * elapsed)
    if critical_heat_flux is not None:
        q = min(q, critical_heat_flux)
    return q / dh_vap


def _substrates():
    from slabx.submodels.ground import Substrate
    return {
        #: Concrete under a liquid hydrogen pool, from PRESLHY E3.4.  The
        #: diffusivity was derived from thermocouples at 4, 9, 14, 54 and
        #: 98 mm and checked against the erfc solution at four times; the
        #: conductivity carries a stated +-30 % from unknown moisture content.
        #:
        #: **This is not warm concrete.**  ``rho cp = k/alpha`` comes out at
        #: 8.0e6 J/(m3 K) against about 1.9e6 for concrete at room
        #: temperature, because the moisture in the pores has frozen and its
        #: latent heat is part of what the cooling front has to remove.  Using
        #: room-temperature properties gives twice the diffusivity and half the
        #: heat flux.
        "concrete_cryogenic": Substrate(
            name="concrete (cryogenic, PRESLHY E3.4)",
            conductivity=2.0, density=2200.0,
            heat_capacity=2.0 / (2.5e-7 * 2200.0)),
    }


#: Substrate properties measured under cryogenic conditions.
SUBSTRATES = None


def substrate(name: str):
    """A substrate whose properties were measured under a cryogenic pool."""
    global SUBSTRATES
    if SUBSTRATES is None:
        SUBSTRATES = _substrates()
    if name not in SUBSTRATES:
        raise ValueError(
            f"unknown substrate {name!r}; have {sorted(SUBSTRATES)}")
    return SUBSTRATES[name]


def vapour_fraction(fluid: str, tanker_barg: float,
                    p_ambient: float = 101325.0) -> float:
    """
    Post-flash vapour mass fraction of saturated liquid at `tanker_barg`
    expanded isenthalpically to `p_ambient`.
    """
    if tanker_barg < 0.0:
        raise ValueError(
            f"tanker_barg is gauge pressure and must be >= 0, "
            f"got {tanker_barg!r}")
    p0 = tanker_barg * 1e5 + p_ambient
    try:
        p_crit = CP.PropsSI("Pcrit", fluid)
    except Exception as exc:                       # unknown fluid
        raise ValueError(f"unknown fluid {fluid!r}") from exc
    if p0 >= p_crit:
        raise ValueError(
            f"stagnation pressure {p0/1e5:.2f} bar is at or above the critical "
            f"pressure of {fluid} ({p_crit/1e5:.2f} bar); there is no "
            f"saturated liquid to flash")
    h0 = CP.PropsSI("H", "P", p0, "Q", 0, fluid)
    q = CP.PropsSI("Q", "P", p_ambient, "H", h0, fluid)
    return min(max(float(q), 0.0), 1.0)


def equilibrium_radius(rate: float, vapour_frac: float, flux: float) -> float:
    """
    Radius [m] at which evaporation balances liquid delivery.

    Returns 0.0 when no liquid reaches the ground, which is a pool that does
    not form rather than an error.
    """
    if rate < 0.0:
        raise ValueError(f"rate must be >= 0, got {rate!r}")
    if not 0.0 <= vapour_frac <= 1.0:
        raise ValueError(
            f"vapour_frac must be in [0, 1], got {vapour_frac!r}")
    if flux <= 0.0:
        raise ValueError(f"flux must be > 0, got {flux!r}")
    m_liquid = rate * (1.0 - vapour_frac)
    if m_liquid <= 0.0:
        return 0.0
    return math.sqrt(m_liquid / (math.pi * flux))


def pool_radius(*, rate: float, tanker_barg: float, fluid: str,
                rho_liquid: float,
                regression_rate: float = REGRESSION_RATE,
                max_radius: float | None = None,
                p_ambient: float = 101325.0) -> dict[str, Any]:
    """
    ``{vapour_fraction, m_liquid, flux, radius, area, confined}``.

    `max_radius` bounds the pool where it is physically confined -- NASA Test 6
    released into a 9.1 m pond with 0.6 m clay walls, so the unconfined radius
    is not what forms.  Leave it unset on flat ground.
    """
    if rate <= 0.0:
        raise ValueError(f"rate must be > 0, got {rate!r}")
    if max_radius is not None and max_radius <= 0.0:
        raise ValueError(f"max_radius must be > 0, got {max_radius!r}")
    x = vapour_fraction(fluid, tanker_barg, p_ambient=p_ambient)
    flux = flux_from_regression(rho_liquid, regression_rate)
    r = equilibrium_radius(rate, x, flux)
    confined = False
    if max_radius is not None and r > max_radius:
        r, confined = max_radius, True
    return {"vapour_fraction": x, "m_liquid": rate * (1.0 - x), "flux": flux,
            "radius": r, "area": math.pi * r * r, "confined": confined}
