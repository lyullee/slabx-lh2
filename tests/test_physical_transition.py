import pytest

from slabx.core.trajectory import Mode
from slabx.submodels.atmosphere import Atmosphere
from slabx_lh2.physical_transition import PhysicalTransitionCloud


@pytest.fixture
def cloud():
    return PhysicalTransitionCloud(
        substance=object(),
        h2_rate=2.0,
        h2_mass_fraction=0.25,
        density_kg_m3=1.0,
        temperature_K=100.0,
        half_width_m=2.0,
        depth_m=1.0,
        centre_height_m=0.5,
        handoff_distance_m=4.0,
        duration_s=5.0,
    )


def test_species_and_carrier_inventories_are_separate(cloud):
    assert cloud.total_mass == pytest.approx(10.0)
    assert cloud.carrier_total_mass == pytest.approx(40.0)
    assert cloud.released_mass(2.0) == pytest.approx(4.0)
    assert cloud.released_mass(10.0) == pytest.approx(10.0)
    assert cloud.carrier_released_mass(2.0) == pytest.approx(16.0)


def test_handoff_state_preserves_mixture_flux_and_composition(cloud):
    atm = Atmosphere(
        u_ref=2.0, z_ref=10.0, T=290.0, rh=50.0, z0=0.01,
        stability="D",
    )
    state = cloud.initial_state(atm, dx=0.1)

    assert state.mode is Mode.PLUME
    assert state.x_start == pytest.approx(4.0)
    assert state.m_emission == pytest.approx(0.25)
    assert state.m_ev == pytest.approx(0.25)
    assert state.R_flux == pytest.approx(4.0)
    assert state.u == pytest.approx(2.0)
    assert state.h == pytest.approx(1.0)


@pytest.mark.parametrize(
    "field,value",
    [("h2_rate", 0.0), ("h2_mass_fraction", 1.0), ("duration_s", -1.0)],
)
def test_invalid_resolved_states_are_rejected(cloud, field, value):
    values = dict(cloud.__dict__)
    values[field] = value
    with pytest.raises(ValueError):
        PhysicalTransitionCloud(**values)
