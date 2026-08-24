"""Shared fixtures. The slow ones actually integrate the model."""

import math

import pytest

pytest.importorskip("slabx")
from slabx.thermo.base import Substance


@pytest.fixture(scope="session")
def h2():
    return Substance(name="H2", mw=0.002016, cp_vapour=14300.0,
                     cp_liquid=9800.0, dh_vap=445000.0, T_boil=20.3,
                     rho_liquid=70.8)


@pytest.fixture(scope="session")
def lng():
    return Substance(name="LNG", mw=0.016043, cp_vapour=2238.0,
                     cp_liquid=3348.5, dh_vap=509900.0, T_boil=111.7,
                     rho_liquid=424.1)


@pytest.fixture(scope="session")
def so2():
    return Substance(name="SO2", mw=0.064066, cp_vapour=622.0,
                     cp_liquid=1360.0, dh_vap=389000.0, T_boil=263.1,
                     rho_liquid=1460.0)


@pytest.fixture(scope="session")
def ffi_nozzle_area():
    """FFI outdoor trials: 1 inch nominal bore."""
    return math.pi * 0.0254 ** 2 / 4
