import pytest


pytest.importorskip("lh2poolx")
pytest.importorskip("slabx")

from lh2poolx import LH2Release, evaluate_pool_source
from slabx.thermo.base import Substance
from slabx_lh2.lh2pool import evaporating_pool_from_lh2pool


def _h2():
    return Substance(name="H2", mw=0.002016, cp_vapour=14300.0,
                     cp_liquid=9800.0, dh_vap=445000.0, T_boil=20.3,
                     rho_liquid=70.8)


def test_adapter_transfers_area_and_evaporation_rate():
    term = evaluate_pool_source(LH2Release(0.1055, 1.0), elapsed_s=300.0)
    source = evaporating_pool_from_lh2pool(term, substance=_h2(), duration=60.0)
    assert source.area == pytest.approx(term.area_m2)
    assert source.rate == pytest.approx(term.evaporation_rate_kg_s)


def test_adapter_refuses_a_confined_source():
    term = evaluate_pool_source(LH2Release(9.5, 0.1, max_radius_m=0.5),
                                elapsed_s=300.0)
    with pytest.raises(ValueError, match="inventory"):
        evaporating_pool_from_lh2pool(term, substance=_h2(), duration=60.0)
