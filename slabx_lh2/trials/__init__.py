"""
Trial conditions, and where the measurements they are compared against live.

Two kinds of number come out of a field trial and they are not distributed the
same way here.

**Conditions** -- release rate, wind speed, temperature, nozzle, duration --
are the experiment's settings. They are in this package, because without them
nobody can run the model at all, and reproducing a model result should not
require anyone to obtain a report.

**Observations** -- arc concentrations, pool radii, temperature traces -- are
the reports' findings. They are **not** in this package. `observations.py`
carries the interface and raises with instructions; `data/SOURCES.md` says
which report each set comes from and `scripts/extract/` turns those reports
back into the CSVs this work used.

So a fresh install reproduces every model output and every internal
comparison, and reproduces the comparisons against measurement once the
reports are obtained. `docs/40_PUBLIC_RELEASE.md` lists exactly which results
fall on which side of that line.
"""

from .conditions import (E35, FFI, NASA, ZHANG, Trial, ffi_source,  # noqa: F401
                         nozzle_area)

__all__ = ["Trial", "FFI", "E35", "NASA", "ZHANG", "ffi_source",
           "nozzle_area"]
