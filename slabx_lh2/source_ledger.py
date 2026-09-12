"""Model-neutral source-state ledger for connecting LH2 source calculations.

The ledger records the physical state handed from a source calculation to a
dispersion model.  It is deliberately not a dispersion model and does not
infer missing impact, droplet, or pool physics.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class SourceState:
    """One source-plane state at elapsed time ``time_s``."""

    time_s: float
    h2_rate_kg_s: float
    h2_mass_fraction: float
    temperature_K: float
    density_kg_m3: float
    area_m2: float
    velocity_m_s: float = 0.0
    liquid_fraction: float = 0.0
    height_m: float = 0.0
    bearing_deg: float = 0.0


@dataclass(frozen=True)
class SourceLedger:
    """Validated, serialisable handoff between a source and a route.

    ``stage`` should identify the physical stage (for example ``flash`` or
    ``near_field_handoff``).  Route adapters must still document their own
    interpretation of the state; this class never silently converts a
    two-phase state into a gas-only source.
    """

    substance: str
    stage: str
    states: tuple[SourceState, ...]
    duration_s: float
    observation_operator: str = "not specified"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.substance.strip():
            raise ValueError("substance must not be empty")
        if not self.stage.strip():
            raise ValueError("stage must not be empty")
        if not self.states:
            raise ValueError("at least one source state is required")
        if self.duration_s <= 0.0:
            raise ValueError("duration_s must be > 0")
        times = [s.time_s for s in self.states]
        if any(t <= 0.0 for t in times) or any(b <= a for a, b in zip(times, times[1:])):
            raise ValueError("states must have strictly increasing positive time_s")
        for s in self.states:
            if s.time_s > self.duration_s:
                raise ValueError("state time exceeds duration_s")
            if not 0.0 <= s.h2_mass_fraction <= 1.0:
                raise ValueError("h2_mass_fraction must be in [0, 1]")
            if not 0.0 <= s.liquid_fraction <= 1.0:
                raise ValueError("liquid_fraction must be in [0, 1]")
            if s.h2_rate_kg_s < 0.0 or s.area_m2 <= 0.0 or s.density_kg_m3 <= 0.0:
                raise ValueError("rate, area, and density must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "substance": self.substance,
            "stage": self.stage,
            "duration_s": self.duration_s,
            "observation_operator": self.observation_operator,
            "metadata": dict(self.metadata),
            "states": [asdict(s) for s in self.states],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SourceLedger":
        states = tuple(SourceState(**row) for row in data["states"])
        return cls(
            substance=str(data["substance"]),
            stage=str(data["stage"]),
            states=states,
            duration_s=float(data["duration_s"]),
            observation_operator=str(data.get("observation_operator", "not specified")),
            metadata=dict(data.get("metadata", {})),
        )

    def write_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "SourceLedger":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def to_evaporating_pool(self, *, substance: Any):
        """Map a quasi-steady single-area ledger to SLAB's pool source.

        This adapter intentionally rejects time-varying area/rate and liquid
        accumulation.  Resolve those with an upstream pool inventory model.
        """
        if self.stage not in {"pool", "near_field_handoff"}:
            raise ValueError("ledger stage is not a pool handoff")
        first = self.states[0]
        if any(abs(s.area_m2 - first.area_m2) > 1e-12 for s in self.states):
            raise ValueError("time-varying pool area needs an inventory model")
        if any(s.liquid_fraction > 1e-12 for s in self.states):
            raise ValueError("liquid-bearing state needs a resolved evaporation handoff")
        from slabx.core.source import EvaporatingPool
        return EvaporatingPool(
            substance=substance,
            rate=first.h2_rate_kg_s,
            area=first.area_m2,
            duration=self.duration_s,
        )


__all__ = ["SourceState", "SourceLedger"]
