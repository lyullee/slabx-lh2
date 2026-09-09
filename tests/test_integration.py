"""
Integration tests: these run the dispersion model.

Two kinds live here.

**Negative controls.** Every module in this package was adopted on the
condition that it leaves the dense-gas and passive limits alone, because those
are what the original SLAB validation rests on. If one of these fails, the
module is a defect regardless of what it does for LH2. They are the first
thing to run and the first thing to believe.

**Characterisation.** The headline numbers, pinned so that a change to the
model is visible rather than silent. When one of these fails it does not
necessarily mean something is broken -- it means the number moved and the
reason has to be written down. The tolerances are loose on purpose: they are
there to catch a factor, not a percent.

Marked `slow`; run with `-m "not slow"` to skip.
"""

import math

import numpy as np
import pytest

pytest.importorskip("slabx")
from slabx.core.plume import run_dispersion
from slabx.core.source import EvaporatingPool, HorizontalJet
from slabx.post.concentration import concentration_field
from slabx.submodels.atmosphere import Atmosphere
from slabx.thermo.base import LegacyThermo, water_backend
from slabx.thermo.coolprop import CoolPropThermo, coolprop_water

from slabx_lh2.diagnostics import briggs_liftoff, premise_summary, rise_scaling
from slabx_lh2.lfl import brackets_from_arcs, flammable_distance, verdict
from slabx_lh2.plume_width import plume_width_coupling
from slabx_lh2.water_ice import clamped, with_sublimation

pytestmark = pytest.mark.slow

#: Burro 8, the stable low-wind LNG pool trial; observed LFL distance 455 m.
BURRO8 = dict(u_ref=1.94, z_ref=3.0, T=290.0, rh=50.0, z0=2e-4,
              stability="E")
BURRO8_SOURCE = dict(rate=116.93, area=116.93 / (116.93 / 657.0),
                     duration=107.0)


def _lng_run(lng, water, coupling):
    atm = Atmosphere(**BURRO8)
    with plume_width_coupling(coupling):
        traj, _ = run_dispersion(EvaporatingPool(substance=lng, **BURRO8_SOURCE),
                                 atm, LegacyThermo(lng), water,
                                 x_max=1000.0, n_puff_steps=40)
    field = concentration_field(traj, atm, z=1.0, t_avg=80.0, t_release=107.0)
    return traj, field.distance_to(0.05)


# --------------------------------------------------------------------------
class TestNegativeControls:
    """These decide whether the modules may be used at all."""

    def test_plume_width_is_bit_identical_on_a_dense_cloud(self, lng):
        water = clamped(coolprop_water())
        _, off = _lng_run(lng, water, False)
        _, on = _lng_run(lng, water, True)
        assert on == off, (
            "the width coupling reached a dense cloud; it is gated on "
            "is_lofted and a dense cloud never lofts")

    def test_legacy_antoine_water_is_corrected_when_requested(self, lng):
        """
        Antoine extrapolation is neither a clamp nor the IAPWS sublimation
        curve. It must not be misclassified as already corrected merely
        because it varies below the triple point.
        """
        stock = water_backend()
        corrected = with_sublimation(stock)
        assert corrected is not stock
        _, a = _lng_run(lng, stock, False)
        _, b = _lng_run(lng, corrected, False)
        assert abs(b - a) / a > 1e-4

    def test_the_water_treatment_effect_is_not_specific_to_hydrogen(self, lng):
        """
        Deliberately reconstruct the old clamp on the same LNG trial and
        compare it with the corrected CoolProp water treatment.

        Burro 8's cloud runs from 208 to 290 K and 25 of its 58 trajectory
        points are below the water triple point, so there is nothing about
        hydrogen in this. Any cryogenic release into humid air that reaches
        for a real-fluid library and gets the clamp is affected.

        This is cross-fluid evidence, not a negative control and not a claim
        that the installed slabx 1.0.6 still has the defect.
        """
        _, stock = _lng_run(lng, clamped(coolprop_water()), False)
        _, fixed = _lng_run(lng, with_sublimation(coolprop_water()), False)
        change = abs(fixed - stock) / stock
        assert change > 0.05, (
            f"the CoolProp water backend now moves by only {change:.1%}; "
            f"the deliberate water-treatment ablation collapsed")

    def test_passive_limit_is_untouched(self, so2):
        atm = Atmosphere(u_ref=4.6, z_ref=2.0, T=300.0, rh=40.0, z0=6e-3,
                         stability="D")
        src = dict(rate=0.09, area=1.0, duration=1200.0)
        out = []
        for water, coupling in ((water_backend(), False),
                                (with_sublimation(water_backend()), True)):
            with plume_width_coupling(coupling):
                traj, _ = run_dispersion(EvaporatingPool(substance=so2, **src),
                                         atm, LegacyThermo(so2), water,
                                         x_max=600.0, n_puff_steps=40)
            out.append(np.asarray(traj.z_c, dtype=float).copy())
        assert np.array_equal(out[0], out[1]), (
            "a passive cloud has zero buoyancy and zero w_c; neither module "
            "should be able to reach it")

    def test_briggs_never_fires_on_a_dense_cloud(self, lng):
        atm = Atmosphere(**BURRO8)
        traj, _ = _lng_run(lng, water_backend(), False)
        assert float(briggs_liftoff(traj, atm).max()) < 1.0


# --------------------------------------------------------------------------
class TestFFI:
    """FFI outdoor trials, Spadeadam 2019. Release height 0.5 m."""

    @staticmethod
    def _trials():
        from slabx_lh2.trials import FFI
        from slabx_lh2.trials import observations as obs
        out = {}
        for k, t in FFI.items():
            try:
                arcs = obs.arc_maxima(k)
            except obs.ObservationsUnavailable:
                pytest.skip("measured arc concentrations are not "
                            "distributed; see data/SOURCES.md")
            out[k] = (t.rate_kg_s, t.liquid_fraction, t.wind_m_s,
                      t.temperature_C, t.duration_s, t.averaging_window_s,
                      arcs)
        return out
    ARCS = (30.0, 50.0, 100.0)

    def _run(self, h2, area, trial, rh=75.0):
        q, liq, u, Tc, dur, win, _ = self._trials()[trial]
        atm = Atmosphere(u_ref=u, z_ref=10.0, T=Tc + 273.15, rh=rh, z0=0.01,
                         stability="D")
        src = HorizontalJet(substance=h2, rate=q, area=area,
                            duration=float(dur), liquid_fraction=liq,
                            height=0.5, T_source=20.37)
        with plume_width_coupling():
            traj, _ = run_dispersion(
                src, atm, CoolPropThermo(h2, fluid="Hydrogen"),
                with_sublimation(coolprop_water()), x_max=300.0,
                n_puff_steps=40)
        return atm, traj, dur, win

    @pytest.mark.parametrize("trial", [1, 3, 4, 7])
    def test_premise_holds(self, h2, ffi_nozzle_area, trial):
        """All four FFI trials are well inside the bent-over premise."""
        _, traj, _, _ = self._run(h2, ffi_nozzle_area, trial)
        s = premise_summary(traj)
        assert not s["violated"], f"w_c/u reached {s['max']:.2f}"
        assert s["max"] < 0.2

    @pytest.mark.parametrize("trial,expected", [
        (1, "in"), (3, "in"), (4, "NOT conservative"), (7, "in")])
    def test_lfl_distance_against_the_measured_bracket(
            self, h2, ffi_nozzle_area, trial, expected):
        """
        Five of six FFI trials fall in the measured bracket and Test 4 does
        not, which is why SAFETY_FACTOR exists. Test 4's failure is pinned
        deliberately: if it ever passes, the factor should be revisited.
        """
        atm, traj, dur, win = self._run(h2, ffi_nozzle_area, trial)
        bracket = brackets_from_arcs(self.ARCS, self._trials()[trial][6])
        d = flammable_distance(traj, atm, t_avg=win, t_release=float(dur),
                               safety_factor=1.0)
        assert verdict(d["raw"], bracket) == expected

    def test_the_safety_factor_makes_every_trial_conservative(
            self, h2, ffi_nozzle_area):
        for trial in self._trials():
            atm, traj, dur, win = self._run(h2, ffi_nozzle_area, trial)
            lo, _ = brackets_from_arcs(self.ARCS, self._trials()[trial][6])
            d = flammable_distance(traj, atm, t_avg=win, t_release=float(dur))
            assert d["factored"] >= lo, (
                f"trial {trial}: {d['factored']:.1f} m below the measured "
                f"lower bound {lo:.1f} m")

    def test_lfl_distance_is_grid_independent(self, h2, ffi_nozzle_area):
        """
        The distance must be the interpolated crossing, not a grid node.
        `slabx` uses a geometric grid, so every run with the same `x_max`
        shares its nodes -- which once made four trials report an identical
        40.75 m. Changing `x_max` changes the cell width; the answer must not
        follow it.
        """
        got = []
        for x_max in (120.0, 300.0, 1200.0):
            q, liq, u, Tc, dur, win, _ = self._trials()[3]
            atm = Atmosphere(u_ref=u, z_ref=10.0, T=Tc + 273.15, rh=75.0,
                             z0=0.01, stability="D")
            src = HorizontalJet(substance=h2, rate=q, area=ffi_nozzle_area,
                                duration=float(dur), liquid_fraction=liq,
                                height=0.5, T_source=20.37)
            with plume_width_coupling():
                traj, _ = run_dispersion(
                    src, atm, CoolPropThermo(h2, fluid="Hydrogen"),
                    with_sublimation(coolprop_water()), x_max=x_max,
                    n_puff_steps=40)
            got.append(flammable_distance(traj, atm, t_avg=win,
                                          t_release=float(dur))["raw"])
        assert max(got) / min(got) < 1.01, got

    def test_the_six_trials_give_six_different_distances(
            self, h2, ffi_nozzle_area):
        """A reviewer will ask why they were once all the same."""
        got = []
        for trial in self._trials():
            atm, traj, dur, win = self._run(h2, ffi_nozzle_area, trial)
            got.append(round(flammable_distance(
                traj, atm, t_avg=win, t_release=float(dur))["raw"], 2))
        assert len(set(got)) == len(got), got

    def test_trial3_lfl_distance_is_stable_between_rh60_and_90(
            self, h2, ffi_nozzle_area):
        """
        The accessible FFI report does not tabulate humidity. This narrow test
        pins one trial over RH 60--90 %; it must not be generalized to the
        full RH 0--100 % sweep, where Tests 1 and 6 move by more than 50 %.
        """
        got = []
        for rh in (60.0, 75.0, 90.0):
            atm, traj, dur, win = self._run(h2, ffi_nozzle_area, 3, rh=rh)
            got.append(flammable_distance(traj, atm, t_avg=win,
                                          t_release=float(dur))["raw"])
        assert max(got) / min(got) < 1.3, f"LFL distances {got}"


# --------------------------------------------------------------------------
class TestNASA:
    """
    Witcofski & Chirivella (1984), White Sands. 5.7 m3 into a 9.1 m pond.

    These are characterisation, not validation: the trials sit far outside the
    bent-over premise and the model is being run somewhere it should not be.
    They are here so that a change to the rise is visible.
    """

    #  test, wind, spill time, T_C, RH
    @staticmethod
    def _trials():
        from slabx_lh2.trials import NASA
        return {k: (t.wind_m_s, t.duration_s, t.temperature_C,
                    t.humidity_pct) for k, t in NASA.items()}

    def _run(self, h2, trial, coupling=True):
        u, ts, Tc, rh = self._trials()[trial]
        atm = Atmosphere(u_ref=u, z_ref=10.0, T=Tc + 273.15, rh=rh, z0=3e-3,
                         stability="D")
        src = EvaporatingPool(substance=h2, rate=5.7 * 70.8 / ts,
                              area=math.pi * 4.55 ** 2, duration=float(ts))
        with plume_width_coupling(coupling):
            traj, _ = run_dispersion(
                src, atm, CoolPropThermo(h2, fluid="Hydrogen"),
                with_sublimation(coolprop_water()), x_max=200.0,
                n_puff_steps=40)
        return atm, traj

    def test_premise_is_violated(self, h2):
        """Documented, so that nobody reads a NASA number as validation."""
        _, traj = self._run(h2, 6)
        s = premise_summary(traj)
        assert s["violated"] and s["max"] > 1.5

    def test_briggs_orders_by_wind_not_by_rate(self, h2):
        """
        The registered prediction P-N1: rank correlation of L_p with wind at
        or below -0.8. Wind and rate are collinear across these four, so what
        this pins is that L_p does not have the sign a rate-driven measure
        would.
        """
        lp = {}
        for t in self._trials():
            atm, traj = self._run(h2, t)
            lp[t] = float(briggs_liftoff(traj, atm).max())
        by_wind = sorted(self._trials(), key=lambda t: self._trials()[t][0])
        got = [lp[t] for t in by_wind]
        assert all(b < a for a, b in zip(got, got[1:])), (
            f"L_p should fall monotonically with wind, got {got}")

    def test_the_rise_exponent_misses_the_registered_band(self, h2):
        """
        Pinned as a failure, on purpose.

        `PREREG_lh2_plume_width` declared the exponent must land in 0.6 - 0.9,
        and it did, on Test 6, before the water correction was adopted. With
        both modules active it does not, on any of the four trials. If this
        ever starts passing, the addendum to that registration is out of date
        and must be revisited rather than quietly left.
        """
        for t in self._trials():
            _, traj = self._run(h2, t)
            n = rise_scaling(traj)["exponent"]
            assert not (0.6 <= n <= 0.9), (
                f"NASA test {t}: exponent {n:.3f} now inside the registered "
                f"band; see docs/prereg/PREREG_lh2_plume_width.md ADDENDUM")

    def test_the_residual_is_explained_by_the_scaling_algebra(self, h2):
        """
        n = 2/(s+1) with s = dlnB/dlnz + dlnh/dlnz, to within 10 %.

        This is what turns "the coupling did not reach the band" into "the
        depth is not coupled to the rise and the width only partway".
        """
        for t in self._trials():
            _, traj = self._run(h2, t)
            r = rise_scaling(traj)
            assert abs(r["exponent_predicted"] / r["exponent"] - 1.0) < 0.10, r
            assert r["dlnh_dlnz"] < 0.6, (
                f"depth now follows the rise ({r['dlnh_dlnz']:.2f}); the "
                f"diagnosis in the addendum would need revisiting")

    def test_the_coupling_still_reduces_the_rise(self, h2):
        """Characterisation: about a factor of two at this scale."""
        tops = {}
        for coupling in (False, True):
            _, traj = self._run(h2, 6, coupling=coupling)
            z = np.asarray(traj.z_c, float)
            h = np.asarray(traj.h, float)
            top = np.where(z > 0.5 * h, z + 0.5 * h, h)
            tops[coupling] = float(np.interp(33.8, traj.x, top))
        assert tops[False] / tops[True] > 1.5, tops


class TestGridIndependence:
    """
    How much the LFL distance moves with where the integration stops.

    **An earlier figure of 0.1 % came from a single trial.** Measured on all
    six it is 0.07 to 1.65 %, and the sensitive one is the trial that lofts:
    where the integration ends changes how much of the rise is resolved.

    Pinned so the number in the documents stays measured rather than
    remembered.
    """

    X_MAX = (120.0, 300.0, 1200.0)

    @pytest.mark.slow
    def test_the_spread_is_under_two_per_cent_on_every_trial(self):
        import numpy as np
        from slabx_lh2.trials import FFI
        worst, worst_t = 0.0, None
        for t in sorted(FFI):
            ds = [self._lfl(t, xm) for xm in self.X_MAX]
            spread = (max(ds) - min(ds)) / float(np.mean(ds)) * 100
            if spread > worst:
                worst, worst_t = spread, t
        assert worst < 2.0, (
            f"trial {worst_t} moves {worst:.2f} % across x_max; the "
            f"documented range is 0.07 to 1.65 %")
        assert worst > 0.5, (
            "the spread has collapsed; either the grid changed or this test "
            "is no longer measuring what it thinks")

    @pytest.mark.slow
    def test_the_lofting_trial_is_the_sensitive_one(self):
        """Test 6 lofts and is an order more sensitive than test 4."""
        import numpy as np
        s = {}
        for t in (4, 6):
            ds = [self._lfl(t, xm) for xm in self.X_MAX]
            s[t] = (max(ds) - min(ds)) / float(np.mean(ds)) * 100
        assert s[6] > 5 * s[4], f"test 6 {s[6]:.2f} %, test 4 {s[4]:.2f} %"

    @staticmethod
    def _lfl(trial, x_max):
        import math
        import warnings
        warnings.simplefilter("ignore")
        from slabx.core.plume import run_dispersion
        from slabx.core.source import HorizontalJet
        from slabx.submodels.atmosphere import Atmosphere
        from slabx.thermo.base import Substance
        from slabx.thermo.coolprop import CoolPropThermo, coolprop_water

        from slabx_lh2.lfl import flammable_distance
        from slabx_lh2.plume_width import plume_width_coupling
        from slabx_lh2.trials import FFI
        from slabx_lh2.water_ice import with_sublimation

        h2 = Substance(name="H2", mw=0.002016, cp_vapour=14300.0,
                       cp_liquid=9800.0, dh_vap=445000.0, T_boil=20.3,
                       rho_liquid=70.8)
        t = FFI[trial]
        atm = Atmosphere(u_ref=t.wind_m_s, z_ref=10.0,
                         T=t.temperature_C + 273.15, rh=75.0, z0=0.01,
                         stability="D")
        src = HorizontalJet(substance=h2, rate=t.rate_kg_s, area=t.area_m2,
                            duration=t.duration_s,
                            liquid_fraction=t.liquid_fraction,
                            height=t.release_height_m, T_source=20.37)
        with plume_width_coupling():
            traj, _ = run_dispersion(src, atm,
                                     CoolPropThermo(h2, fluid="Hydrogen"),
                                     with_sublimation(coolprop_water()),
                                     x_max=x_max, n_puff_steps=40)
        return flammable_distance(traj, atm, t_avg=t.averaging_window_s,
                                  t_release=t.duration_s,
                                  safety_factor=1.0)["raw"]


class TestRFluxIsAHalfFlux:
    """
    `Trajectory.R_flux` is a **half-plume** mass flux.

    SLAB integrates one side of a symmetric cloud, so the total is
    `2 * R_flux`. Reading it as the total halves every entrainment ratio
    derived from it, which is what happened in an earlier revision of
    `docs/52`: 127.3 kg/s where the total is 254.6, and an excess of 1.7
    where it is 2.5.

    The check is exact at the source, where the total must equal the release
    rate.
    """

    @pytest.mark.parametrize("trial", [1, 3, 4, 5, 6, 7])
    def test_twice_the_source_flux_is_the_release_rate(self, trial):
        import math
        import warnings
        warnings.simplefilter("ignore")

        import numpy as np
        from slabx.core.plume import run_dispersion
        from slabx.core.source import HorizontalJet
        from slabx.submodels.atmosphere import Atmosphere
        from slabx.thermo.base import Substance
        from slabx.thermo.coolprop import CoolPropThermo, coolprop_water

        from slabx_lh2.trials import FFI
        from slabx_lh2.water_ice import with_sublimation

        h2 = Substance(name="H2", mw=0.002016, cp_vapour=14300.0,
                       cp_liquid=9800.0, dh_vap=445000.0, T_boil=20.3,
                       rho_liquid=70.8)
        t = FFI[trial]
        atm = Atmosphere(u_ref=t.wind_m_s, z_ref=10.0,
                         T=t.temperature_C + 273.15, rh=75.0, z0=0.01,
                         stability="D")
        src = HorizontalJet(substance=h2, rate=t.rate_kg_s, area=t.area_m2,
                            duration=t.duration_s,
                            liquid_fraction=t.liquid_fraction,
                            height=t.release_height_m, T_source=20.37)
        traj, _ = run_dispersion(src, atm,
                                 CoolPropThermo(h2, fluid="Hydrogen"),
                                 with_sublimation(coolprop_water()),
                                 x_max=50.0, n_puff_steps=20)
        total = 2.0 * float(np.asarray(traj.R_flux)[0])
        assert total == pytest.approx(t.rate_kg_s, rel=1e-12), (
            f"2 * R_flux[0] is {total}, release rate {t.rate_kg_s}; the "
            f"half-flux convention has changed and every entrainment ratio "
            f"derived from R_flux is wrong by that factor")

    @pytest.mark.slow
    def test_the_reported_excess_uses_the_total(self):
        """Test 6 at 30 m: 254.6 kg/s, not 127.3."""
        import numpy as np
        import sys
        import pathlib
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent
                               / "scripts"))
        import entrainment_uncertainty as EU
        traj, _ = EU.run_trial(6)
        assert EU.total_flux(traj, 30.0) == pytest.approx(254.6, abs=1.0)
