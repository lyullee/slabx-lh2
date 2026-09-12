"""
slabx-lh2 -- liquid hydrogen extensions to the SLAB dense-gas dispersion model.

What is here, and what each thing rests on:

    water_ice     a compatibility correction for slabx 1.0.4 and the partial
                  1.0.5 fix. slabx 1.0.6 already supplies both the IAPWS
                  sublimation curve and water fusion enthalpy. Behavioural
                  checks apply only the missing part and prevent double
                  addition. A deliberate clamped-versus-corrected LNG
                  ablation moves Burro 8 by 13.5 %; that is cross-fluid
                  evidence, not a defect in the installed 1.0.6 backend.

    plume_width   a missing coupling. A lofted cloud keeps a ground-level
                  width, so its rise has no inertia to stop it. Adding the
                  plume-spread term takes the rise exponent from 1.22 to 0.87
                  against Briggs's 0.67. Bit-identical on every trial that
                  does not loft.

    pool          historical LH2 pool-radius consistency checks and a local
                  ground-conduction source term.  This is not an independent,
                  general pool-formation validation.

    lh2pool       optional adapter from the standalone LH2PoolX source-term
                  package.  It passes an explicitly qualified unconfined pool
                  to SLAB; it does not resolve jet impact or pool inventory.

    depth_cap     **rejected, twice.** The depth is three times the passive
                  limit at 30 m and that is the whole of the horizontal-jet
                  under-prediction, so the target is real. But a ceiling
                  measured from the source crushes a pool release -- sigma_z
                  is 0.09 m at 1 m -- and the dense-gas set moves by 36 %.
                  Kept for the record, and for `fired_count`, which exists
                  because a control once passed while this code did nothing.

    vertical_drag **exploratory.** The form drag on a plume as a bluff body,
                  from Mack & Boot's extension of EFFECTS (JLP 2023) with
                  their published coefficients. A second, independent
                  mechanism against the over-rise, carried for comparison and
                  **not adopted**: with both corrections active the rise
                  exponent lands in the registered band on one of four NASA
                  trials.

    diagnostics   `w_c/u`, which says when the x-marching formulation is
                  outside its own premise, and Briggs's `L_p`, which orders
                  clouds by how readily they lift. Neither changes a
                  prediction; both are reported.

    lfl           the distance to 4 vol%, which is what a separation distance
                  is set from. At the manuscript's assumed RH of 75 %, the
                  1.25 factor makes all six FFI trials conservative; the
                  un-factored bracket count is humidity-dependent.

What is **not** here, and why, is as much of the result: multiple hypotheses
were pre-registered and rejected, including ground reflection, cloud depth,
pre-lift-off vertical drag, rise-dependent entrainment, added mass, and an
impinging-jet source. See `docs/24_LH2_SUMMARY.md`.
"""

__version__ = "0.1.5"

from . import (depth_cap, diagnostics, lfl, lh2pool, plume_width, pool,  # noqa: F401
               vertical_drag,
               water_ice)
from .source_ledger import SourceLedger, SourceState

__all__ = ["diagnostics", "lfl", "lh2pool", "plume_width", "pool", "vertical_drag",
           "water_ice", "SourceLedger", "SourceState", "__version__"]
