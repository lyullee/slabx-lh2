"""
What the trials measured. **Not distributed with this package.**

Why not
-------
The conditions in `conditions.py` are the experiments' settings, and without
them nobody could run the model at all. These are the reports' findings, which
belong to the organisations that ran the trials, and redistributing them is
their decision rather than this project's.

Nothing here is secret. Every set is obtainable, most of them freely, and
`data/SOURCES.md` says which report each comes from and what to extract.
`scripts/extract/` then turns those reports back into the CSVs this work used,
so a reader who wants the comparisons can reproduce them exactly rather than
approximately.

What this costs you
-------------------
Everything that is a model output or an internal comparison runs without any
of this: the water-saturation defect, the dense-gas negative controls, the
applicability diagnostic and its screening curve, the runtime benchmark, the
ablation, the applicability map. Those are the grade-A results and they are
the paper's two main claims.

What needs the observations is the comparison against measurement -- the LFL
bracket verdicts, the pool radii, the RR986 temperature field. Grade B and C.

    docs/40_PUBLIC_RELEASE.md   which result falls on which side
    data/SOURCES.md             how to obtain each set

Installing them
---------------
Extract the reports into CSVs with `scripts/extract/`, then either point
`SLABX_LH2_DATA` at the directory holding them or drop them in `data/`.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

__all__ = ["ObservationsUnavailable", "data_dir", "available", "arc_maxima",
           "pool_radii", "SOURCES"]

#: dataset -> (report, how to get it, what to extract)
SOURCES: dict[str, tuple[str, str, str]] = {
    "ffi_arcs": (
        "FFI-RAPPORT 20/03101, appendix A",
        "public PDF from FFI (Norwegian Defence Research Establishment)",
        "maximum concentration at the 30, 50 and 100 m arcs; "
        "scripts/extract/parse_ffi.py"),
    "e35_farfield": (
        "PRESLHY E3.5, DOI 10.35097/1481",
        "CC BY-SA 4.0, KITopen",
        "far-field stand concentrations; scripts/extract/extract_e35_v2.py. "
        "**Sensors saturate at 4 vol%**; the saturated column marks it"),
    "e34_pool": (
        "PRESLHY E3.4, DOI 10.35097/1319",
        "KITopen, registration required",
        "scale mass and in-substrate temperatures; "
        "scripts/extract/extract_e34.py"),
    "rr986_ground": (
        "HSE RR986, figure 15",
        "public PDF from the Health and Safety Executive",
        "concrete temperatures at 10, 20 and 30 mm; digitised by hand, "
        "about +-5 K"),
    "nasa_arcs": (
        "Witcofski & Chirivella (1984), Int. J. Hydrogen Energy 9, 425",
        "publisher; the paper states it is a US Government work not subject "
        "to copyright",
        "tables 3 and 4"),
}


class ObservationsUnavailable(RuntimeError):
    """Raised when a measurement set is asked for and is not installed."""

    def __init__(self, key: str) -> None:
        report, access, what = SOURCES.get(
            key, ("unknown", "see data/SOURCES.md", ""))
        super().__init__(
            f"the measurements for {key!r} are not distributed with this "
            f"package.\n"
            f"  source : {report}\n"
            f"  access : {access}\n"
            f"  extract: {what}\n"
            f"Put the resulting CSV in data/, or set SLABX_LH2_DATA to the "
            f"directory holding it. See data/SOURCES.md.")


def data_dir() -> Path:
    """Where the extracted CSVs are looked for."""
    env = os.environ.get("SLABX_LH2_DATA")
    if env:
        return Path(env).expanduser()
    return Path(__file__).resolve().parent.parent.parent / "data"


def available(key: str) -> bool:
    """Whether a measurement set is installed, without raising."""
    return _path(key).exists()


def _path(key: str) -> Path:
    return data_dir() / {
        "ffi_arcs": "lh2_ffi_sensors.csv",
        "e35_farfield": "lh2_e35_farfield_v2.csv",
        "e34_pool": "lh2_e34_rates.csv",
    }.get(key, f"{key}.csv")


def arc_maxima(trial: int) -> tuple[float, float, float]:
    """
    Maximum concentration [vol %] at the 30, 50 and 100 m arcs of an FFI
    trial, from the extracted sensor file.
    """
    path = _path("ffi_arcs")
    if not path.exists():
        raise ObservationsUnavailable("ffi_arcs")
    by_arc: dict[float, list[float]] = {}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("kind") != "concentration":
                continue
            if int(row["test"]) != trial:
                continue
            by_arc.setdefault(float(row["R_m"]), []).append(float(row["max"]))
    try:
        return tuple(max(by_arc[r]) for r in (30., 50., 100.))  # type: ignore
    except KeyError as exc:
        raise ObservationsUnavailable("ffi_arcs") from exc


def pool_radii() -> dict[str, float]:
    """
    Reported pool radii [m], for the equilibrium-radius comparison.

    Six values across four campaigns, each read from its report. They are
    coarse: FFI quote a range of 0.5 to 1.0 m across seven trials rather than
    a value per trial, and RR986's two trials at the same rate give 0.83 and
    1.13 m, a 36 % spread. **The comparison is quoted to two decimals and the
    measurements are not that good.**
    """
    raise ObservationsUnavailable("pool_radii")
