"""Plume-width coupling, pool radius, and the two diagnostics."""

import math

import numpy as np
import pytest

pytest.importorskip("slabx")
import slabx.core.plume as _plume                                # noqa: E402

from slabx_lh2 import diagnostics, plume_width                    # noqa: E402
from slabx_lh2.pool import (equilibrium_radius, flux_from_regression,
                           pool_radius, vapour_fraction)         # noqa: E402


# --------------------------------------------------------------------------
class TestPlumeWidthPatching:
    """The patch is a module-global swap; it must not survive the block."""

    def test_context_manager_restores(self):
        before = _plume.entrainment
        with plume_width.plume_width_coupling():
            assert plume_width.is_enabled()
        assert _plume.entrainment is before

    def test_restores_on_exception(self):
        before = _plume.entrainment
        with pytest.raises(RuntimeError):
            with plume_width.plume_width_coupling():
                raise RuntimeError("boom")
        assert _plume.entrainment is before

    def test_nests(self):
        before = _plume.entrainment
        with plume_width.plume_width_coupling():
            with plume_width.plume_width_coupling(active=False):
                assert not plume_width.is_enabled()
            assert plume_width.is_enabled()
        assert _plume.entrainment is before

    def test_inactive_block_is_a_no_op(self):
        before = _plume.entrainment
        with plume_width.plume_width_coupling(active=False):
            assert _plume.entrainment is before
        assert _plume.entrainment is before

    def test_enable_disable_round_trip(self):
        before = _plume.entrainment
        plume_width.enable()
        plume_width.enable()
        plume_width.disable()
        assert _plume.entrainment is before


# --------------------------------------------------------------------------
class TestPoolRadius:
    def test_mass_balance(self):
        # pi R^2 E = q (1-x)
        r = equilibrium_radius(rate=1.0, vapour_frac=0.0, flux=1.0 / math.pi)
        assert r == pytest.approx(1.0)

    def test_all_vapour_gives_no_pool(self):
        assert equilibrium_radius(rate=1.0, vapour_frac=1.0, flux=0.07) == 0.0

    def test_scales_as_sqrt_rate(self):
        a = equilibrium_radius(1.0, 0.0, 0.07)
        b = equilibrium_radius(4.0, 0.0, 0.07)
        assert b / a == pytest.approx(2.0)

    @pytest.mark.parametrize("kwargs", [
        {"rate": -1.0, "vapour_frac": 0.5, "flux": 0.07},
        {"rate": 1.0, "vapour_frac": 1.5, "flux": 0.07},
        {"rate": 1.0, "vapour_frac": -0.1, "flux": 0.07},
        {"rate": 1.0, "vapour_frac": 0.5, "flux": 0.0},
    ])
    def test_rejects_nonsense(self, kwargs):
        with pytest.raises(ValueError):
            equilibrium_radius(**kwargs)

    def test_flux_from_regression(self):
        assert flux_from_regression(70.8, 1e-3) == pytest.approx(0.0708)
        with pytest.raises(ValueError):
            flux_from_regression(-1.0)

    def test_vapour_fraction_rises_with_pressure(self):
        x = [vapour_fraction("Hydrogen", b) for b in (0.8, 2.0, 6.0, 10.0)]
        assert all(b > a for a, b in zip(x, x[1:]))
        assert 0.0 < x[0] < x[-1] < 1.0

    def test_vapour_fraction_rejects_vacuum(self):
        with pytest.raises(ValueError, match="gauge"):
            vapour_fraction("Hydrogen", -0.5)

    def test_vapour_fraction_rejects_supercritical(self):
        with pytest.raises(ValueError, match="critical"):
            vapour_fraction("Hydrogen", 100.0)

    def test_vapour_fraction_rejects_unknown_fluid(self):
        with pytest.raises(ValueError, match="unknown fluid"):
            vapour_fraction("Unobtainium", 1.0)

    @pytest.mark.parametrize("rate,barg,observed", [
        (0.1055, 1.0, 0.70),     # E3.5 trial 7
        (0.2650, 5.0, 1.20),     # E3.5 trial 13
        (0.2250, 2.0, 0.75),     # FFI Test 1
        (0.1620, 0.8, 0.75),     # FFI Test 7
    ])
    def test_reproduces_reported_radii_within_a_factor_of_two(
            self, rate, barg, observed):
        """The calibration of PREREG_lh2_impinging; median ratio 1.11."""
        got = pool_radius(rate=rate, tanker_barg=barg, fluid="Hydrogen",
                          rho_liquid=70.8)["radius"]
        assert 0.5 < got / observed < 2.0

    def test_confinement(self):
        free = pool_radius(rate=9.5, tanker_barg=0.1, fluid="Hydrogen",
                           rho_liquid=70.8)
        held = pool_radius(rate=9.5, tanker_barg=0.1, fluid="Hydrogen",
                           rho_liquid=70.8, max_radius=4.55)
        assert free["radius"] > 4.55
        assert held["radius"] == pytest.approx(4.55)
        assert held["confined"] and not free["confined"]

    def test_rejects_zero_rate(self):
        with pytest.raises(ValueError, match="rate"):
            pool_radius(rate=0.0, tanker_barg=1.0, fluid="Hydrogen",
                        rho_liquid=70.8)


# --------------------------------------------------------------------------
class _Traj:
    """Minimal stand-in carrying only what the diagnostics read."""

    def __init__(self, x, w_c, u, h, rho):
        self.x = np.asarray(x, float)
        self.w_c = np.asarray(w_c, float)
        self.u = np.asarray(u, float)
        self.h = np.asarray(h, float)
        self.rho = np.asarray(rho, float)
        self.u_ambient_mean = self.u


class _Atm:
    def __init__(self, rho=1.2, u_star=0.3):
        self.rho = rho
        self.u_star = u_star


class TestPremiseRatio:
    def test_ratio_and_angle(self):
        t = _Traj([1, 2], [1.0, 3.0], [1.0, 1.0], [1, 1], [1.0, 1.0])
        s = diagnostics.premise_summary(t)
        assert s["max"] == pytest.approx(3.0)
        assert s["angle_deg"] == pytest.approx(math.degrees(math.atan(3.0)))
        # the threshold is strict: a ratio of exactly 1 is not a violation
        assert s["violated"] and s["n_violating"] == 1
        assert s["x_first"] == pytest.approx(2.0)

    def test_source_region_is_masked(self):
        t = _Traj([-5, 1], [99.0, 0.1], [1.0, 1.0], [1, 1], [1.0, 1.0])
        assert diagnostics.premise_summary(t)["max"] == pytest.approx(0.1)

    def test_zero_wind_does_not_raise(self):
        t = _Traj([1], [1.0], [0.0], [1], [1.0])
        assert math.isfinite(diagnostics.premise_summary(t)["max"])

    def test_grounded_case_is_not_flagged(self):
        t = _Traj([1, 2], [0.02, 0.03], [6.7, 6.7], [1, 1], [1.0, 1.0])
        assert not diagnostics.premise_summary(t)["violated"]

    def test_critical_wind_scaling(self):
        a, b = diagnostics.CRITICAL_WIND_FIT["D"]
        assert diagnostics.critical_wind(9.5) == pytest.approx(a * 9.5 ** b)
        assert diagnostics.critical_wind(30.0) > diagnostics.critical_wind(0.3)
        with pytest.raises(ValueError):
            diagnostics.critical_wind(0.0)

    def test_critical_wind_rises_with_stability(self):
        """A stable layer suppresses the rise, so more wind is needed."""
        got = [diagnostics.critical_wind(9.5, s) for s in "ABCDEF"]
        assert all(b > a for a, b in zip(got, got[1:])), got
        assert got[-1] / got[0] > 2.0        # F is more than twice A

    def test_critical_wind_rejects_unknown_class(self):
        with pytest.raises(ValueError, match="stability"):
            diagnostics.critical_wind(1.0, "Z")


class TestApplicabilityStatus:
    """The runtime API a monitoring loop calls."""

    def _traj(self, ratio):
        return _Traj([1, 2], [0.0, ratio], [1.0, 1.0], [1, 1], [1.0, 1.0])

    @pytest.mark.parametrize("ratio,status", [
        (0.05, "VALID"), (0.7, "MARGINAL"), (3.0, "OUT_OF_SCOPE")])
    def test_bands(self, ratio, status):
        assert diagnostics.applicability(self._traj(ratio))["status"] == status

    def test_only_out_of_scope_demands_a_fallback(self):
        for ratio, want in ((0.05, False), (0.7, False), (3.0, True)):
            got = diagnostics.applicability(self._traj(ratio))
            assert got["fallback_required"] is want

    def test_reason_is_populated_and_quantitative(self):
        got = diagnostics.applicability(self._traj(3.0))
        assert "3.0" in got["reason"] or "3.00" in got["reason"]
        assert got["premise_ratio"] == pytest.approx(3.0)

    def test_rejects_inverted_bands(self):
        with pytest.raises(ValueError):
            diagnostics.applicability(self._traj(1.0), marginal=2.0,
                                      threshold=1.0)


class TestAirCondensation:
    """Measured, so that not modelling it is a decision rather than a guess."""

    @pytest.mark.parametrize("species", ["N2", "O2"])
    def test_onset_is_above_the_flammable_range(self, species):
        from slabx_lh2.air_condensation import UFL_HYDROGEN, condensation_onset
        got = condensation_onset(species=species)
        assert got["onset_mol_pct"] > UFL_HYDROGEN
        assert got["inside_flammable_range"] is False

    def test_condensation_makes_the_cloud_lighter_not_heavier(self):
        """Latent heat and the loss of heavy species both lower the density."""
        from slabx_lh2.air_condensation import adiabatic_mix
        permanent = adiabatic_mix(0.7, allow_air=False)
        condensing = adiabatic_mix(0.7, allow_air=True)
        assert condensing["condensed"]["N2"] > 0.0
        assert condensing["rho_ratio"] < permanent["rho_ratio"]
        assert condensing["T"] > permanent["T"]

    def test_no_effect_inside_the_flammable_range(self):
        from slabx_lh2.air_condensation import adiabatic_mix
        a = adiabatic_mix(0.25, allow_air=False)
        b = adiabatic_mix(0.25, allow_air=True)
        assert b["y_h2"] < 90.0
        assert b["condensed"]["N2"] == 0.0
        assert b["rho_ratio"] == pytest.approx(a["rho_ratio"], rel=1e-6)

    def test_supercritical_species_cannot_condense(self):
        """N2 above 126.2 K and O2 above 154.6 K have no saturation line."""
        import math
        from slabx_lh2.air_condensation import p_saturation
        assert math.isinf(p_saturation("N2", 200.0))
        assert math.isinf(p_saturation("O2", 200.0))
        assert math.isfinite(p_saturation("N2", 70.0))

    def test_sublimation_below_the_triple_point(self):
        from slabx_lh2.air_condensation import p_saturation
        assert p_saturation("N2", 60.0) < p_saturation("N2", 63.151)
        assert p_saturation("N2", 40.0) < p_saturation("N2", 60.0)


class TestBriggs:
    def test_definition(self):
        t = _Traj([1], [0.0], [1.0], [10.0], [0.6])
        lp = diagnostics.briggs_liftoff(t, _Atm(rho=1.2, u_star=0.5))
        assert lp[0] == pytest.approx(9.80665 * 10.0 * 0.5 / 0.25)

    def test_dense_cloud_gives_zero(self):
        t = _Traj([1], [0.0], [1.0], [10.0], [2.0])
        assert diagnostics.briggs_liftoff(t, _Atm())[0] == 0.0

    def test_scales_as_inverse_u_star_squared(self):
        t = _Traj([1], [0.0], [1.0], [10.0], [0.6])
        a = diagnostics.briggs_liftoff(t, _Atm(u_star=0.2))[0]
        b = diagnostics.briggs_liftoff(t, _Atm(u_star=0.4))[0]
        assert a / b == pytest.approx(4.0)

    def test_refuses_a_meaningless_friction_velocity(self):
        t = _Traj([1], [0.0], [1.0], [10.0], [0.6])
        with pytest.raises(ValueError, match="friction velocity"):
            diagnostics.briggs_liftoff(t, _Atm(u_star=1e-9))

    def test_grounded_thinning_bounds(self):
        assert diagnostics.grounded_thinning(0.0) == pytest.approx(1.0)
        assert 0.0 < diagnostics.grounded_thinning(1.0) < 1.0
        assert diagnostics.grounded_thinning(10.0) < \
            diagnostics.grounded_thinning(1.0)

    def test_grounded_thinning_ignores_negatives(self):
        assert diagnostics.grounded_thinning(-1.0) == pytest.approx(1.0)


# --------------------------------------------------------------------------
class TestVerticalDrag:
    """Mack & Boot's form drag, and the patching it needs."""

    def test_cylinder_value_at_unit_aspect_ratio(self):
        from slabx_lh2.vertical_drag import CD0_CONTINUOUS, drag_coefficient
        assert drag_coefficient(1.0) == pytest.approx(CD0_CONTINUOUS)

    def test_rises_towards_a_flat_plate(self):
        from slabx_lh2.vertical_drag import (CD0_CONTINUOUS, CD1_CONTINUOUS,
                                             drag_coefficient)
        assert drag_coefficient(0.0) == pytest.approx(
            CD0_CONTINUOUS + CD1_CONTINUOUS)
        assert drag_coefficient(0.5) > drag_coefficient(1.0)

    def test_clipped_above_unity(self):
        """Taller than wide is past the crossflow analogy; hold at cylinder."""
        from slabx_lh2.vertical_drag import drag_coefficient
        assert drag_coefficient(5.0) == pytest.approx(drag_coefficient(1.0))

    @pytest.mark.parametrize("ar", [-1.0, float("nan")])
    def test_rejects_nonsense(self, ar):
        from slabx_lh2.vertical_drag import drag_coefficient
        with pytest.raises(ValueError):
            drag_coefficient(ar)

    def test_patches_both_names(self):
        """
        `core.plume` does `from ..submodels.entrainment import fluxes`, so it
        holds its own reference. Patching the submodule alone had exactly zero
        effect and the run looked fine.
        """
        import slabx.core.plume as _p
        import slabx.submodels.entrainment as _e
        from slabx_lh2.vertical_drag import vertical_drag
        before = (_e.fluxes, _p.fluxes)
        with vertical_drag():
            assert _e.fluxes is _p.fluxes
            assert _e.fluxes is not before[0]
        assert (_e.fluxes, _p.fluxes) == before

    def test_restores_on_exception(self):
        import slabx.core.plume as _p
        from slabx_lh2.vertical_drag import vertical_drag
        before = _p.fluxes
        with pytest.raises(RuntimeError):
            with vertical_drag():
                raise RuntimeError("boom")
        assert _p.fluxes is before

    def test_force_is_zero_for_a_sinking_or_grounded_cloud(self):
        from slabx_lh2.vertical_drag import drag_force

        class _C:
            w_c, b_half, h, u, rho, is_puff = -1.0, 5.0, 2.0, 5.0, 1.0, False

        class _A:
            rho = 1.2
        assert drag_force(_C(), _A()) == 0.0

    def test_force_opposes_the_rise_and_grows_as_w_squared(self):
        from slabx_lh2.vertical_drag import drag_force

        class _A:
            rho = 1.2

        def f(w):
            class _C:
                w_c, b_half, h, u, rho, is_puff = w, 5.0, 2.0, 100.0, 1.0, False
            return drag_force(_C(), _A())
        assert f(1.0) < 0.0
        # u is large so cos^2(phi) ~ 1 and the scaling is clean
        assert f(2.0) / f(1.0) == pytest.approx(4.0, rel=0.02)


# --------------------------------------------------------------------------
class TestGroundConduction:
    """
    Against PRESLHY E3.4 Table 3, experiment 20200423-Concrete02.

    Four vaporisation periods with measured mass-loss rates on a 0.25 m2
    concrete pool. The target is a measured mass flux, and the pool sits in a
    box, so nothing about dispersion enters -- this is the cleanest
    non-concentration target in the whole set.
    """

    #  label, t0, t_end [s], measured dm/dt [g/s]; time origin is 500 s
    TABLE3 = [("First", 683.0, 716.0, 15.91), ("Second", 856.0, 893.0, 15.73),
              ("Third", 949.5, 1073.5, 10.95),
              ("Fourth", 1180.5, 1295.5, 9.58)]
    AREA, DH_VAP, T0, TS = 0.25, 445e3, 282.0, 20.0

    def _predicted(self, t0, t_end):
        from slabx_lh2.pool import ground_limited_flux, substrate
        mid = 0.5 * (t0 + t_end) - 500.0
        f = ground_limited_flux(substrate("concrete_cryogenic"), self.DH_VAP,
                                self.T0, self.TS, mid)
        return f * self.AREA * 1e3          # g/s

    @pytest.mark.parametrize("label,t0,t_end,measured", TABLE3)
    def test_within_the_reports_own_uncertainty(self, label, t0, t_end,
                                                measured):
        """E3.4 states +-30 % on the conductivity from unknown moisture."""
        got = self._predicted(t0, t_end)
        assert 0.7 < got / measured < 1.5, f"{label}: {got:.2f} vs {measured}"

    def test_falls_with_time_as_the_ground_cools(self):
        got = [self._predicted(t0, te) for _, t0, te, _ in self.TABLE3]
        assert got[0] > got[-1]
        assert got[-1] / got[0] == pytest.approx(0.52, abs=0.1)

    def test_cryogenic_properties_differ_from_warm_concrete(self):
        """
        The correction that mattered. Room-temperature concrete has 2.6 times
        the diffusivity, because the pore moisture has not frozen, and gives
        half the heat flux.
        """
        from slabx.submodels.ground import Substrate
        from slabx_lh2.pool import substrate
        warm = Substrate(name="warm", conductivity=1.28, density=2200.0,
                         heat_capacity=880.0)
        cold = substrate("concrete_cryogenic")
        assert warm.diffusivity / cold.diffusivity > 2.0

    def test_critical_heat_flux_caps_the_early_divergence(self):
        from slabx_lh2.pool import (CRITICAL_HEAT_FLUX, ground_limited_flux,
                                    substrate)
        s = substrate("concrete_cryogenic")
        capped = ground_limited_flux(s, self.DH_VAP, self.T0, self.TS, 1.0)
        free = ground_limited_flux(s, self.DH_VAP, self.T0, self.TS, 1.0,
                                   critical_heat_flux=None)
        assert capped * self.DH_VAP == pytest.approx(CRITICAL_HEAT_FLUX)
        assert free > capped * 4.0

    def test_the_cap_stops_binding_at_about_24_seconds(self):
        """E3.4 gives 24.1 s; the model must agree without being told."""
        from slabx_lh2.pool import ground_limited_flux, substrate
        s = substrate("concrete_cryogenic")

        def binds(t):
            a = ground_limited_flux(s, self.DH_VAP, self.T0, self.TS, t)
            b = ground_limited_flux(s, self.DH_VAP, self.T0, self.TS, t,
                                    critical_heat_flux=None)
            return a < b - 1e-12
        assert binds(20.0) and not binds(30.0)

    def test_unknown_substrate_is_refused(self):
        from slabx_lh2.pool import substrate
        with pytest.raises(ValueError, match="unknown substrate"):
            substrate("cheese")


# --------------------------------------------------------------------------
class TestConcurrency:
    """
    These patches rebind a module-level name, which is process-global. Two
    threads cannot hold it in different states, and the point of the guard is
    that they find out by an exception rather than by getting each other's
    physics.
    """

    @pytest.mark.parametrize("module", ["plume_width", "vertical_drag"])
    def test_a_second_thread_is_refused(self, module):
        import importlib
        import threading
        import time
        m = importlib.import_module(f"slabx_lh2.{module}")
        cm = getattr(m, "plume_width_coupling" if module == "plume_width"
                     else "vertical_drag")
        caught = []

        def worker():
            try:
                with cm(False):
                    time.sleep(0.05)
            except m.ConcurrentPatchError:
                caught.append(True)

        with cm(True):
            t = threading.Thread(target=worker)
            t.start()
            t.join()
        assert caught, "the second thread silently got the first thread's state"

    @pytest.mark.parametrize("module", ["plume_width", "vertical_drag"])
    def test_the_same_thread_may_nest(self, module):
        import importlib
        m = importlib.import_module(f"slabx_lh2.{module}")
        cm = getattr(m, "plume_width_coupling" if module == "plume_width"
                     else "vertical_drag")
        with cm(True):
            with cm(False):
                pass
        with cm():
            pass                       # released cleanly

    @pytest.mark.parametrize("module", ["plume_width", "vertical_drag"])
    def test_the_guard_releases_on_an_exception(self, module):
        import importlib
        import threading
        m = importlib.import_module(f"slabx_lh2.{module}")
        cm = getattr(m, "plume_width_coupling" if module == "plume_width"
                     else "vertical_drag")
        with pytest.raises(RuntimeError):
            with cm():
                raise RuntimeError("boom")
        # a fresh thread must now be able to take it
        ok = []

        def worker():
            with cm():
                ok.append(True)
        t = threading.Thread(target=worker)
        t.start()
        t.join()
        assert ok, "the guard was not released"


class TestAspectRatio:
    """
    `B` in Mack & Boot is the full projected width, not the half-width.

    Two independent readings fix it: `AR = 1` is stated to be the circular
    cylinder, which needs `H` and `B` to be the same kind of measure, and the
    cylinder drag convention is `C_d (rho/2) v^2 D` with `D` the diameter.
    slabx carries the half-width, so both places take a factor of two.
    """

    class _C:
        w_c, b_half, h, u, rho, is_puff = 2.0, 4.0, 4.0, 1e6, 1.0, False

    class _A:
        rho = 1.2

    def test_a_circular_section_gets_the_cylinder_coefficient(self):
        """h = 2 b_half is a circle, and must give AR = 1."""
        from slabx_lh2.vertical_drag import CD0_CONTINUOUS, drag_force

        class _C:
            w_c, u, rho, is_puff = 1.0, 1e6, 1.0, False
            b_half, h = 3.0, 6.0            # full width 6 = height 6

        class _A:
            rho = 1.2
        expected = CD0_CONTINUOUS * 0.5 * 1.2 * 1.0 * 6.0
        assert drag_force(_C(), _A()) == pytest.approx(-expected, rel=1e-6)

    def test_a_flat_cloud_gets_more_drag_than_a_round_one(self):
        from slabx_lh2.vertical_drag import drag_force

        class _A:
            rho = 1.2

        def f(b_half, h):
            class _C:
                w_c, u, rho, is_puff = 1.0, 1e6, 1.0, False
            _C.b_half, _C.h = b_half, h
            return -drag_force(_C(), _A())
        round_ = f(3.0, 6.0)               # AR = 1
        flat = f(30.0, 6.0)                # AR = 0.1, and ten times as wide
        assert flat / round_ > 10.0        # wider and a higher coefficient


# --------------------------------------------------------------------------
class TestRR986Ground:
    """
    The E3.4 substrate properties applied, unadjusted, to a different concrete.

    Two questions, and they have different answers. Whether the semi-infinite
    assumption holds on an outdoor slab -- it does, much better than in E3.4's
    insulated box. And whether the properties transfer -- they do not.

    Digitised from RR986 Figure 15 at about +-5 K; these bounds are loose
    enough that the digitising cannot be what fails them.
    """

    def _module(self):
        import importlib.util
        import pathlib
        root = pathlib.Path(__file__).resolve().parent.parent
        spec = importlib.util.spec_from_file_location(
            "_rr986", root / "scripts" / "rr986_ground.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def test_the_slab_is_much_closer_to_semi_infinite_than_the_box(self):
        """
        E3.4's 100 mm insulated bed drifts by 4.3x across depth; document 29
        attributed that to the geometry rather than to the model. An outdoor
        slab should drift far less, and that is the check on the attribution.
        """
        m = self._module()
        inverted = []
        for x, (T0, pts) in m.TRACES.items():
            vals = [a for t, T in pts if t <= m.T_POOL_END
                    for a in [m.alpha_from(T, T0, x, t - m.T_POOL_START)]
                    if a is not None]
            if vals:
                vals.sort()
                inverted.append(vals[len(vals) // 2])
        drift = max(inverted) / min(inverted)
        assert drift < 2.5, f"depth drift {drift:.2f}x"

    def test_the_properties_do_not_transfer(self):
        """
        Pinned as a failure. The E3.4 concrete predicts RR986's slab with a
        systematic bias many times the digitising uncertainty, and the paper
        must not claim the substrate properties are general.
        """
        import math
        from slabx_lh2.pool import substrate
        m = self._module()
        sub = substrate("concrete_cryogenic")
        res = [m.erfc_temperature(x, t - m.T_POOL_START, sub.diffusivity, T0)
               - T
               for x, (T0, pts) in m.TRACES.items()
               for t, T in pts if t <= m.T_POOL_END]
        bias = sum(res) / len(res)
        assert bias > 4 * m.SIGMA_T_K, (
            f"bias {bias:.1f} K is now within digitising uncertainty; "
            f"docs/33 needs revisiting")
        assert math.isfinite(bias)

    def test_the_inverted_diffusivity_is_several_times_the_model(self):
        m = self._module()
        from slabx_lh2.pool import substrate
        sub = substrate("concrete_cryogenic")
        for x, (T0, pts) in m.TRACES.items():
            vals = [a for t, T in pts if t <= m.T_POOL_END
                    for a in [m.alpha_from(T, T0, x, t - m.T_POOL_START)]
                    if a is not None]
            if not vals:
                continue
            vals.sort()
            assert vals[len(vals) // 2] / sub.diffusivity > 2.0
