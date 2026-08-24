"""
slabx-lh2 -- liquid hydrogen extensions to the SLAB dense-gas dispersion model.

What is here, and what each thing rests on:

    water_ice     a defect fix. `CoolPropThermo` clamps water saturation at the
                  triple point, so water does not condense in a cryogenic
                  cloud; the error against IAPWS is a factor of 4136 at 200 K.
                  Replaced by the IAPWS sublimation curve. Zero free
                  parameters. Changes the dense-gas set by at most 0.25 %.

    plume_width   a missing coupling. A lofted cloud keeps a ground-level
                  width, so its rise has no inertia to stop it. Adding the
                  plume-spread term takes the rise exponent from 1.22 to 0.87
                  against Briggs's 0.67. Bit-identical on every trial that
                  does not loft.

    pool          the pool radius is not free: evaporation balances delivery.
                  Median predicted/observed 1.11 on six reported radii, and the
                  evaporative flux comes from the model's own ground module
                  rather than from a literature constant.

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
                  is set from, with the 1.25 factor that makes all six FFI
                  trials conservative.

What is **not** here, and why, is as much of the result: eight hypotheses were
pre-registered and rejected, including ground reflection, cloud depth,
pre-lift-off vertical drag, rise-dependent entrainment, added mass, and an
impinging-jet source. See `docs/24_LH2_SUMMARY.md`.
"""

__version__ = "0.1.0"

from . import (diagnostics, lfl, plume_width, pool, vertical_drag,  # noqa: F401
               water_ice)

__all__ = ["diagnostics", "lfl", "plume_width", "pool", "vertical_drag",
           "water_ice", "__version__"]
