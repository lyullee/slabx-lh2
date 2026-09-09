"""
Distance to the flammable limit, which is what a separation distance is set
from.

Sensor concentrations are not the only quantity a risk assessment uses, and
humidity matters to both concentration and distance.  The accessible FFI
report does not tabulate relative humidity.  Across an RH 0--100 % sweep the
two horizontal trials remain under-predicted, but Tests 1 and 6 move by 54 and
57 % in LFL distance and the bracket count changes from three to five of six.
Every quoted bracket count therefore has to carry its assumed humidity.

Verification against the FFI outdoor trials, whose three arcs bracket the
measured LFL distance:

    test  orientation  q [kg/s]  u [m/s]   measured        model    verdict
      1   down           0.225      3.2     0 - 30 m      25.49 m   in
      3   down           0.730      5.8    30 - 50        42.32     in
      4   horizontal     0.828      6.7    50 - 100       44.89     NOT conservative
      5   down           0.715      5.2    30 - 50        43.56     in
      6   horizontal     0.832      2.7    30 - 50        40.77     in
      7   down           0.162      6.5     0 - 30        26.01     in

**Five of six, and the one failure is on the non-conservative side.**

`SAFETY_FACTOR` is **1.25**.  The minimum required by these six is **1.114**;
1.25 was **examined** as a rounded engineering margin.  It was derived and
evaluated on the same six trials, so it is **not an independently validated
safety factor** and must not be described as one.  No other dataset brackets an LFL distance: E3.5 has two arcs
at 10 and 14 m with sensors that saturate at 4 vol%, and NASA reports cloud
heights rather than distances.  Say "sufficient for the six trials
considered", not "validated".

**There is no regulatory factor to compare this against.** An earlier
draft of this work cited "PHMSA's 2.5 for LNG"; that is wrong. 49 CFR
193.2059(b)(1) sets an *average gas concentration in air of 2.5 percent* as
the dispersion endpoint, which is a concentration and not a distance
multiplier. The two have different dimensions and the comparison has been
withdrawn.

Before using the distance, check `slabx_lh2.diagnostics.premise_summary`: below
`critical_wind(rate)` the marching formulation is outside its own premise and
the number should not be used at all, factor or no factor.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Sequence

import numpy as np

from slabx.post.concentration import concentration_field

__all__ = ["LFL_HYDROGEN", "SAFETY_FACTOR", "flammable_distance",
           "brackets_from_arcs"]

#: Lower flammability limit of hydrogen in air [vol %].
LFL_HYDROGEN = 4.0
#: Legacy 0.1.3 same-set exploration value.  It is not independently
#: validated or recommended for new analyses; pass ``safety_factor=1.0`` and
#: report ``raw``.  The symbol is retained for DOI/API reproducibility.
SAFETY_FACTOR = 1.25

_DEFAULT_HEIGHTS = (0.1, 1.0, 1.8)


def _crossing(x, c, level):
    """
    Furthest `x` at which `c` crosses `level`, interpolated.

    Returning the last grid node above the level instead is wrong by up to the
    cell width. `slabx` integrates on a geometric grid, so the cells are ~15 %
    wide and every run with the same `x_max` and `n_puff_steps` shares them --
    which made four FFI trials with visibly different conditions report an
    identical 40.75 m. The number was the grid, not the physics.

    Concentration decays close to a power law downwind, so the interpolation
    is linear in log-log; that is exact for a power law and second-order for
    anything smooth. Falls back to linear where a value is non-positive.
    """
    good = np.isfinite(x) & np.isfinite(c)
    x, c = x[good], c[good]
    above = np.where(c >= level)[0]
    if above.size == 0:
        return None
    i = int(above[-1])
    if i + 1 >= len(c):                 # still above at the last node
        return float(x[i])
    x0, x1, c0, c1 = float(x[i]), float(x[i + 1]), float(c[i]), float(c[i + 1])
    if c0 <= 0.0 or c1 <= 0.0 or x0 <= 0.0 or x1 <= 0.0 or c0 == c1:
        if c0 == c1:
            return x0
        t = (level - c0) / (c1 - c0)
        return x0 + t * (x1 - x0)
    t = (math.log(level) - math.log(c0)) / (math.log(c1) - math.log(c0))
    return math.exp(math.log(x0) + t * (math.log(x1) - math.log(x0)))


def flammable_distance(traj, atm, *, t_avg: float, t_release: float,
                       level: float = LFL_HYDROGEN,
                       heights: Sequence[float] = _DEFAULT_HEIGHTS,
                       safety_factor: float = SAFETY_FACTOR,
                       coeffs: Any = None) -> dict[str, Any]:
    """
    Furthest downwind distance [m] at which any sampled height reaches `level`.

    Returns ``{raw, factored, level, heights, reached}``.  `reached` is False
    when the cloud never reaches the level at any sampled height, in which case
    both distances are 0.0 -- a cloud that is never flammable, not a failure.

    The 0.1.3 default multiplier is a legacy same-set exploratory value, not a
    validated safety factor.  New analyses should pass ``safety_factor=1.0``
    and report ``raw`` unless an independently justified factor is supplied.

    The maximum is taken over `heights` rather than at one height because a
    lofted cloud can exceed the limit above the ground while a grounded one
    does not; taking one height would make the answer depend on which.
    """
    if level <= 0.0:
        raise ValueError(f"level must be > 0, got {level!r}")
    if safety_factor < 1.0:
        raise ValueError(
            f"safety_factor must be >= 1 to be conservative, "
            f"got {safety_factor!r}")
    if not heights:
        raise ValueError("heights must not be empty")
    if t_release <= 0.0:
        raise ValueError(f"t_release must be > 0, got {t_release!r}")

    best = 0.0
    reached = False
    for z in heights:
        if z < 0.0:
            raise ValueError(f"heights must be >= 0, got {z!r}")
        kw = {"z": float(z), "t_avg": float(t_avg),
              "t_release": float(t_release)}
        if coeffs is not None:
            kw["coeffs"] = coeffs
        field = concentration_field(traj, atm, **kw)
        d = _crossing(np.asarray(field.x, dtype=float),
                      np.asarray(field.peak, dtype=float) * 100.0, level)
        if d is not None:
            reached = True
            best = max(best, d)
    return {"raw": best, "factored": best * safety_factor if reached else 0.0,
            "level": level, "heights": tuple(heights), "reached": reached}


def brackets_from_arcs(arc_distances: Sequence[float],
                       arc_maxima: Sequence[float],
                       level: float = LFL_HYDROGEN
                       ) -> tuple[float, float]:
    """
    Bound the measured LFL distance from concentrations on a set of arcs.

    Returns ``(lower, upper)``; `upper` is `math.inf` when the outermost arc is
    still above the limit, meaning the measurement did not reach far enough to
    bound it.
    """
    d = list(map(float, arc_distances))
    c = list(map(float, arc_maxima))
    if len(d) != len(c):
        raise ValueError("arc_distances and arc_maxima must be the same length")
    if len(d) < 2:
        raise ValueError("need at least two arcs to bracket a crossing")
    if any(b <= a for a, b in zip(d, d[1:])):
        raise ValueError("arc_distances must be strictly increasing")
    if c[0] < level:
        return (0.0, d[0])
    for i in range(len(d) - 1):
        if c[i] >= level > c[i + 1]:
            return (d[i], d[i + 1])
    return (d[-1], math.inf)


def verdict(model_distance: float, bracket: tuple[float, float]) -> str:
    """``in`` / ``conservative`` / ``NOT conservative``."""
    lo, hi = bracket
    if lo <= model_distance <= hi:
        return "in"
    return "conservative" if model_distance > hi else "NOT conservative"
