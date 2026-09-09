"""Optional adapter from LH2PoolX source terms to SLAB ``EvaporatingPool``."""

from __future__ import annotations


def evaporating_pool_from_lh2pool(pool_source, *, substance, duration: float):
    """Build a SLAB source from one evidence-qualified LH2PoolX time window.

    The caller chooses the time window and duration.  A confined result is
    refused because its positive liquid accumulation requires a separate pool
    inventory calculation before it can be represented as a steady source.
    """
    if duration <= 0.0:
        raise ValueError("duration must be > 0")
    if pool_source.source_status != "quasi_steady_equilibrium":
        raise ValueError(
            "LH2PoolX source is not a quasi-steady unconfined pool; "
            "resolve its inventory before passing it to SLAB"
        )
    from slabx.core.source import EvaporatingPool

    return EvaporatingPool(
        substance=substance,
        rate=pool_source.evaporation_rate_kg_s,
        area=pool_source.area_m2,
        duration=duration,
    )
