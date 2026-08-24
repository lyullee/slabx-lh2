"""
What each trial was set to. No measured results here.

Sources for the settings themselves, which are tabulated in the reports:

    FFI     FFI-RAPPORT 20/03101, tables 2.2 to 2.8
    E3.5    PRESLHY, DOI 10.35097/1481, conditions sheet
    NASA    Witcofski & Chirivella (1984), Int. J. Hydrogen Energy 9, table 1
    Zhang   Zhang et al. (2024), Appl. Sci. 14, 3645, table 1

Two of these carry a caveat that changes what may be concluded, so they are
recorded on the objects rather than in prose someone might not read.

**FFI never reported humidity.** It was measured by DNV and does not appear in
the public report. Every FFI run here assumes a value; the arc-concentration
statistics swing from FAC2 0.42 to 0.92 across a plausible range, while the
LFL distance does not move. That is why this work decides on the distance.

**NASA never reported the pool radius**, only the 9.1 m pond it was released
into. `pond_radius_m` is first-hand; the 2 to 3 m pool that EFFECTS cite is
not in the original paper, and the rise exponent depends on which is used.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

__all__ = ["Trial", "FFI", "E35", "NASA", "ZHANG", "nozzle_area",
           "ffi_source"]


def nozzle_area(diameter_mm: float) -> float:
    """Circular area [m2] from a bore in millimetres."""
    if diameter_mm <= 0.0:
        raise ValueError(f"diameter must be > 0, got {diameter_mm!r}")
    return math.pi * (diameter_mm / 1000.0) ** 2 / 4


@dataclass(frozen=True)
class Trial:
    """
    One trial's settings.

    `humidity_pct` is `None` where the campaign did not report it, so that an
    assumed value has to be supplied deliberately rather than by default.
    """

    campaign: str
    label: str
    rate_kg_s: float
    wind_m_s: float
    wind_ref_height_m: float
    temperature_C: float
    duration_s: float
    orientation: str = "horizontal"
    source_type: str = "jet"
    humidity_pct: float | None = None
    liquid_fraction: float | None = None
    release_height_m: float = 0.0
    nozzle_mm: float | None = None
    pool_radius_m: float | None = None
    roughness_m: float = 0.01
    stability: str = "D"
    averaging_window_s: float | None = None
    note: str = ""

    @property
    def area_m2(self) -> float:
        if self.nozzle_mm is not None:
            return nozzle_area(self.nozzle_mm)
        if self.pool_radius_m is not None:
            return math.pi * self.pool_radius_m ** 2
        raise ValueError(f"{self.label}: neither a nozzle nor a pool radius")


#: FFI outdoor trials, Spadeadam 2019. Humidity is not in the public report.
FFI: dict[int, Trial] = {
    1: Trial("FFI", "test1", 0.225, 3.2, 10.0, 1.0, 780.0,
             orientation="vertical down", liquid_fraction=0.888,
             release_height_m=0.5, nozzle_mm=25.4, averaging_window_s=800.0),
    3: Trial("FFI", "test3", 0.730, 5.8, 10.0, 2.9, 900.0,
             orientation="vertical down", liquid_fraction=0.559,
             release_height_m=0.5, nozzle_mm=25.4, averaging_window_s=400.0),
    4: Trial("FFI", "test4", 0.828, 6.7, 10.0, 3.3, 360.0,
             liquid_fraction=0.559, release_height_m=0.5, nozzle_mm=25.4,
             averaging_window_s=310.0),
    5: Trial("FFI", "test5", 0.715, 5.2, 10.0, 3.7, 240.0,
             orientation="vertical down", liquid_fraction=0.559,
             release_height_m=0.5, nozzle_mm=25.4, averaging_window_s=200.0,
             note="two minutes unignited, a valve closure, two more "
                  "unignited, then ignition; the unignited release is 240 s, "
                  "not the 360 s run time"),
    6: Trial("FFI", "test6", 0.832, 2.7, 10.0, 3.8, 180.0,
             liquid_fraction=0.559, release_height_m=0.5, nozzle_mm=25.4,
             averaging_window_s=150.0, note="ignited after the unignited "
                                            "phase"),
    7: Trial("FFI", "test7", 0.162, 6.5, 10.0, 3.2, 480.0,
             orientation="vertical down", liquid_fraction=0.949,
             release_height_m=0.5, nozzle_mm=25.4, averaging_window_s=350.0),
}

#: NASA White Sands, 5.7 m3 into a 9.1 m diameter pond.
NASA: dict[int, Trial] = {
    2: Trial("NASA", "test2", 5.7 * 70.8 / 40, 1.6, 10.0, 24.0, 40.0,
             orientation="ground spill", source_type="pool",
             humidity_pct=49.0, pool_radius_m=4.55, roughness_m=3e-3,
             note="pond radius, not pool radius; the original does not "
                  "report the pool"),
    4: Trial("NASA", "test4", 5.7 * 70.8 / 33, 3.6, 10.0, 15.0, 33.0,
             orientation="ground spill", source_type="pool",
             humidity_pct=43.0, pool_radius_m=4.55, roughness_m=3e-3),
    5: Trial("NASA", "test5", 5.7 * 70.8 / 24, 6.3, 10.0, 12.0, 24.0,
             orientation="ground spill", source_type="pool",
             humidity_pct=43.0, pool_radius_m=4.55, roughness_m=3e-3),
    6: Trial("NASA", "test6", 5.7 * 70.8 / 35, 2.2, 10.0, 15.0, 35.0,
             orientation="ground spill", source_type="pool",
             humidity_pct=29.0, pool_radius_m=4.55, roughness_m=3e-3),
}

#: Zhang et al. (2024), the eight trials that report a duration.
ZHANG: dict[int, Trial] = {
    5: Trial("Zhang 2024", "test5", 3.0 * 70.8 / 4, 0.13, 10.0, 18.58, 4.0,
             orientation="ground spill", source_type="pool",
             humidity_pct=28.83, pool_radius_m=3.385),
    6: Trial("Zhang 2024", "test6", 2.5 * 70.8 / 40, 0.30, 10.0, 9.39, 40.0,
             orientation="ground spill", source_type="pool",
             humidity_pct=39.76, pool_radius_m=3.385),
    7: Trial("Zhang 2024", "test7", 2.5 * 70.8 / 30, 0.04, 10.0, 4.61, 30.0,
             orientation="ground spill", source_type="pool",
             humidity_pct=27.63, pool_radius_m=3.385),
    8: Trial("Zhang 2024", "test8", 2.5 * 70.8 / 48, 0.05, 10.0, 6.02, 48.0,
             orientation="ground spill", source_type="pool",
             humidity_pct=29.21, pool_radius_m=3.385),
    9: Trial("Zhang 2024", "test9", 1.5 * 70.8 / 25, 0.61, 10.0, 9.91, 25.0,
             orientation="ground spill", source_type="pool",
             humidity_pct=27.46, pool_radius_m=3.385),
    10: Trial("Zhang 2024", "test10", 3.0 * 70.8 / 4, 0.11, 10.0, 8.90, 4.0,
              orientation="ground spill", source_type="pool",
              humidity_pct=46.11, pool_radius_m=3.385),
    11: Trial("Zhang 2024", "test11", 3.0 * 70.8 / 5, 0.01, 10.0, 34.67, 5.0,
              orientation="ground spill", source_type="pool",
              humidity_pct=79.55, pool_radius_m=3.385),
    12: Trial("Zhang 2024", "test12", 0.5 * 70.8 / 20, 0.15, 10.0, 34.52,
              20.0, orientation="ground spill", source_type="pool",
              humidity_pct=67.13, pool_radius_m=3.385),
}

#: PRESLHY E3.5 far-field trials, nominal table flow rates.
#: The dataset also records a flow meter whose peak and mean differ from the
#: table by up to 30 % and 60 %; the Briggs ordering is insensitive to which
#: is used (-0.891 to -0.936 across the three).
_E35_SETUP = {"3.5.1": ("h", 0.5, 25.4, 1), "3.5.2": ("h", 0.5, 12, 1),
              "3.5.4": ("h", 1.5, 25.4, 1), "3.5.5": ("h", 1.5, 12, 1),
              "3.5.7": ("u", 0.5, 12, 1), "3.5.8": ("d", 0.5, 12, 1),
              "3.5.10": ("h", 0.5, 25.4, 5), "3.5.11": ("h", 0.5, 12, 5),
              "3.5.12": ("h", 0.5, 6, 5), "3.5.13": ("h", 1.5, 25.4, 5),
              "3.5.14": ("h", 1.5, 12, 5), "3.5.15": ("h", 1.5, 6, 5),
              "3.5.16": ("u", 0.5, 12, 5), "3.5.17": ("d", 0.5, 12, 5)}
_E35_TRIAL = {3: "3.5.1", 4: "3.5.2", 6: "3.5.7", 7: "3.5.8", 8: "3.5.8",
              10: "3.5.10", 11: "3.5.11", 12: "3.5.12", 13: "3.5.17",
              14: "3.5.16", 16: "3.5.4", 17: "3.5.5", 19: "3.5.4",
              20: "3.5.5", 22: "3.5.13", 23: "3.5.14", 24: "3.5.15"}
_E35_FLOW = {(25.4, 1): 0.1395, (12, 1): 0.1055, (25.4, 5): 0.298,
             (12, 5): 0.265, (6, 5): 0.095}
#: trial -> wind [m/s], T [C], RH [%]
_E35_MET = {3: (3.60, 4.0, 76.0), 4: (1.83, 4.0, 76.0), 6: (2.50, 4.4, 74.0),
            7: (2.37, 4.4, 74.0), 8: (2.47, 4.4, 74.0), 10: (2.700, 5.1, 71.0),
            11: (1.50, 5.1, 71.0), 12: (1.93, 5.1, 71.0), 13: (4.17, 5.6, 69.),
            14: (2.87, 5.6, 69.0), 16: (3.90, 4.0, 76.0), 17: (2.50, 4.0, 76.),
            19: (1.60, 4.0, 76.0), 20: (0.57, 4.0, 76.0), 22: (1.70, 5.6, 69.),
            23: (1.70, 5.6, 69.0), 24: (1.90, 5.6, 69.0)}
_ORIENT = {"h": "horizontal", "u": "vertical up", "d": "vertical down"}

E35: dict[int, Trial] = {}
for _t, _name in _E35_TRIAL.items():
    _ori, _hgt, _d, _bar = _E35_SETUP[_name]
    _u, _T, _rh = _E35_MET[_t]
    E35[_t] = Trial("PRESLHY E3.5", f"trial{_t}", _E35_FLOW[(_d, _bar)], _u,
                    1.5, _T, 120.0, orientation=_ORIENT[_ori],
                    source_type="pool" if _ori == "d" else "jet",
                    humidity_pct=_rh, release_height_m=_hgt,
                    nozzle_mm=None if _ori == "d" else _d,
                    pool_radius_m=(1.2 if _t == 13 else 0.7)
                    if _ori == "d" else None,
                    note=f"{_name}, {_bar} barg")


def ffi_source(trial: int, substance, *, humidity_pct: float = 75.0):
    """
    A `HorizontalJet` for an FFI trial, with the humidity supplied explicitly.

    The keyword has no silent default in `Trial` because FFI did not report
    it; passing it here is the caller stating an assumption.
    """
    from slabx.core.source import HorizontalJet
    from slabx.submodels.atmosphere import Atmosphere
    t = FFI[trial]
    atm = Atmosphere(u_ref=t.wind_m_s, z_ref=t.wind_ref_height_m,
                     T=t.temperature_C + 273.15, rh=humidity_pct,
                     z0=t.roughness_m, stability=t.stability)
    src = HorizontalJet(substance=substance, rate=t.rate_kg_s,
                        area=t.area_m2, duration=t.duration_s,
                        liquid_fraction=t.liquid_fraction,
                        height=t.release_height_m, T_source=20.37)
    return src, atm, t
