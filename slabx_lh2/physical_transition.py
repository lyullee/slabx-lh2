"""Resolved LH2 jet-to-cloud handoff for the SLABx dispersion core.

The adapter preserves mixture flux, composition, temperature and geometry at
an upstream physical handoff plane.  Its finite-release clock deliberately
tracks H2 inventory, while the already entrained H2+air carrier inventory is
available through separate properties.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhysicalTransitionCloud:
    """Pre-diluted cloud state at a model-determined physical handoff plane."""

    substance: object
    h2_rate: float
    h2_mass_fraction: float
    density_kg_m3: float
    temperature_K: float
    half_width_m: float
    depth_m: float
    centre_height_m: float
    handoff_distance_m: float
    duration_s: float
    cp_h2_j_kgk: float = 14300.0
    cp_air_j_kgk: float = 1006.0
    name: str = "physical_transition_cloud"
    scalar_core_fraction: float = 0.9
    vertical_velocity_m_s: float = 0.0
    velocity_override_m_s: float | None = None

    def __post_init__(self) -> None:
        positive = (
            "h2_rate", "density_kg_m3", "temperature_K", "half_width_m",
            "depth_m", "handoff_distance_m", "duration_s",
        )
        for field in positive:
            if getattr(self, field) <= 0:
                raise ValueError(f"{field} must be positive")
        if not 0 < self.h2_mass_fraction < 1:
            raise ValueError("h2_mass_fraction must lie in (0, 1)")
        if not 0 < self.scalar_core_fraction < 1:
            raise ValueError("scalar_core_fraction must lie in (0, 1)")
        if self.velocity_override_m_s is not None and self.velocity_override_m_s <= 0:
            raise ValueError("velocity_override_m_s must be positive when set")

    @property
    def total_rate(self) -> float:
        """H2+air mixture rate at the handoff plane [kg/s]."""
        return self.h2_rate / self.h2_mass_fraction

    @property
    def rate(self) -> float:
        """Emitted-species rate used by the SLABx source contract [kg/s]."""
        return self.h2_rate

    @property
    def T(self) -> float:
        return self.temperature_K

    @property
    def liquid_fraction(self) -> float:
        return 0.0

    @property
    def duration(self) -> float:
        return self.duration_s

    @property
    def air_rate(self) -> float:
        return self.total_rate - self.h2_rate

    @property
    def area_m2(self) -> float:
        return 2.0 * self.half_width_m * self.depth_m

    @property
    def velocity_m_s(self) -> float:
        if self.velocity_override_m_s is not None:
            return self.velocity_override_m_s
        return self.total_rate / (self.density_kg_m3 * self.area_m2)

    @property
    def cp_j_kgk(self) -> float:
        return (
            self.h2_mass_fraction * self.cp_h2_j_kgk
            + (1.0 - self.h2_mass_fraction) * self.cp_air_j_kgk
        )

    @property
    def total_mass(self) -> float:
        """Released H2 inventory used by the plume-to-puff clock [kg]."""
        return self.h2_rate * self.duration_s

    @property
    def carrier_total_mass(self) -> float:
        """Total H2+air carrier inventory crossing the handoff plane [kg]."""
        return self.total_rate * self.duration_s

    @property
    def half_width(self) -> float:
        return self.half_width_m

    def expanded(self, half_width: float) -> "PhysicalTransitionCloud":
        """Return the resolved source unchanged; upstream geometry is fixed."""
        return self

    def released_mass(self, t: float) -> float:
        """H2 inventory released by time ``t`` [kg]."""
        return self.h2_rate * min(max(t, 0.0), self.duration_s)

    def carrier_released_mass(self, t: float) -> float:
        """H2+air carrier inventory crossing the plane by time ``t`` [kg]."""
        return self.total_rate * min(max(t, 0.0), self.duration_s)

    def flux(self, x: float, t: float):
        """No distributed source remains downstream of the handoff plane."""
        from slabx.core.source import SourceFlux

        return SourceFlux()

    def initial_state(self, atm, *, dx: float, **_kw):
        """Build the conserved SLABx state at the handoff plane."""
        from slabx.core.source import SourceState, _mean_wind
        from slabx.core.trajectory import Mode

        return SourceState(
            x_start=self.handoff_distance_m,
            t_start=0.0,
            mode=Mode.PLUME,
            h=self.depth_m,
            z_c=self.centre_height_m,
            b_half=self.half_width_m,
            b_shape=self.scalar_core_fraction * self.half_width_m,
            b_half_x=1.0,
            b_shape_x=1.0,
            u=self.velocity_m_s,
            T=self.temperature_K,
            rho=self.density_kg_m3,
            cp=self.cp_j_kgk,
            m_emission=self.h2_mass_fraction,
            m_ev=self.h2_mass_fraction,
            m_water=0.0,
            m_wv=0.0,
            u_ambient_mean=_mean_wind(
                atm, self.centre_height_m + 0.5 * self.depth_m
            ),
            R_flux=0.5 * self.total_rate,
            w_c=self.vertical_velocity_m_s,
        )
