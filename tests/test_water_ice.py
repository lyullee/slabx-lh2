"""Water saturation below the triple point."""

import math

import pytest

from slabx_lh2.water_ice import (DH_FUSION, P_TRIPLE, T_TRIPLE,
                                SublimationWater, correction_state,
                                p_sublimation, with_sublimation)

pytest.importorskip("slabx")
from slabx.thermo.base import water_backend                     # noqa: E402
from slabx.thermo.coolprop import coolprop_water                # noqa: E402


def _upstream_fixed() -> bool:
    """
    Whether the installed slabx already carries the correction.

    **slabx 1.0.6 adopted it.** The tests below that pin the defect can only
    run against a version that has it, so they are skipped rather than failed
    — a passing suite on 1.0.6 has to mean "the defect is gone", not "the
    tests were deleted".
    """
    from slabx_lh2.water_ice import already_corrected
    return already_corrected(coolprop_water())


needs_defect = pytest.mark.skipif(
    _upstream_fixed(),
    reason="the installed slabx already corrects water below the triple "
           "point (1.0.6 and later); there is no defect here to pin")
needs_fix = pytest.mark.skipif(
    not _upstream_fixed(),
    reason="the installed slabx still clamps (1.0.4 and earlier); "
           "slabx_lh2 supplies the correction instead")


def magnus_over_ice(T):
    """Reference approximation, for order-of-magnitude checks only."""
    return 611.657 * math.exp(22.587 * (T - 273.16) / (T - 0.7))


class TestSublimationCurve:
    def test_anchored_at_the_triple_point(self):
        assert p_sublimation(T_TRIPLE) == pytest.approx(P_TRIPLE, rel=1e-9)

    @pytest.mark.parametrize("T", [270.0, 260.0, 250.0, 240.0, 230.0, 200.0])
    def test_within_a_few_percent_of_the_reference(self, T):
        assert p_sublimation(T) == pytest.approx(magnus_over_ice(T), rel=0.07)

    def test_monotone(self):
        Ts = [50.0, 100.0, 150.0, 200.0, 240.0, 270.0, T_TRIPLE]
        ps = [p_sublimation(T) for T in Ts]
        assert all(b > a for a, b in zip(ps, ps[1:]))

    def test_underflows_to_zero_rather_than_raising(self):
        assert p_sublimation(1.0) == 0.0
        assert p_sublimation(4.0) == 0.0

    def test_rejects_above_the_triple_point(self):
        # the correlation does not diverge there, it quietly returns a wrong
        # number, which is the dangerous failure
        with pytest.raises(ValueError, match="triple point"):
            p_sublimation(300.0)

    @pytest.mark.parametrize("T", [float("nan"), float("inf")])
    def test_rejects_non_finite(self, T):
        with pytest.raises(ValueError, match="finite"):
            p_sublimation(T)


@needs_defect
class TestTheDefectItself:
    """
    The clamp is what this package existed to fix; pin it down.

    Skipped against slabx 1.0.6 and later, which fixed it upstream. The
    numbers stay here because they are the record of what the defect was.
    """

    def test_stock_backend_is_flat_below_the_triple_point(self):
        w = coolprop_water()
        assert w.saturation_ratio(200.0) == pytest.approx(
            w.saturation_ratio(150.0), rel=1e-12)

    def test_stock_backend_error_at_200_K_is_three_orders(self):
        w = coolprop_water()
        ratio = w.saturation_ratio(200.0) * 101325.0 / p_sublimation(200.0)
        assert ratio > 1000.0

    def test_wrapper_removes_it(self):
        w = with_sublimation(coolprop_water())
        assert w.saturation_ratio(200.0) < w.saturation_ratio(240.0)
        assert w.saturation_ratio(240.0) < w.saturation_ratio(270.0)


class TestWrapperContract:
    def test_does_not_mutate_the_backend_it_wraps(self):
        stock = coolprop_water()
        before = stock.saturation_ratio(200.0)
        with_sublimation(stock)
        assert stock.saturation_ratio(200.0) == before

    def test_is_idempotent(self):
        once = with_sublimation(coolprop_water())
        twice = with_sublimation(once)
        assert twice is once
        # the heat of fusion must not be added twice
        assert twice.dh_vap(200.0) == pytest.approx(once.dh_vap(200.0))

    @needs_defect
    def test_adds_fusion_below_and_not_above(self):
        """Against a clamped backend, which is what the wrapper is for."""
        stock = coolprop_water()
        w = with_sublimation(stock)
        assert w.dh_vap(200.0) == pytest.approx(
            stock.dh_vap(200.0) + DH_FUSION)
        assert w.dh_vap(290.0) == pytest.approx(stock.dh_vap(290.0))

    def test_delegates_everything_else(self):
        stock = coolprop_water()
        w = with_sublimation(stock)
        assert w.name == stock.name
        assert w.rho_liquid == stock.rho_liquid
        assert w.cp_vapour(250.0) == stock.cp_vapour(250.0)

    def test_derivative_is_positive_and_finite(self):
        w = with_sublimation(coolprop_water())
        for T in (150.0, 200.0, 240.0, 270.0):
            d = w.d_saturation_ratio(T)
            assert math.isfinite(d) and d > 0.0

    def test_continuous_across_the_triple_point(self):
        w = with_sublimation(coolprop_water())
        below = w.saturation_ratio(T_TRIPLE - 1e-3)
        above = w.saturation_ratio(T_TRIPLE + 1e-3)
        assert below == pytest.approx(above, rel=0.05)

    def test_rejects_nonsense_ambient_pressure(self):
        with pytest.raises(ValueError, match="p_ambient"):
            SublimationWater(coolprop_water(), p_ambient=0.0)

    def test_wraps_the_legacy_backend_too(self):
        stock = water_backend()
        w = with_sublimation(stock)
        assert w is not stock
        assert w.saturation_ratio(200.0) * 101325.0 == pytest.approx(
            p_sublimation(200.0), rel=0.01)

    def test_pressure_only_upstream_fix_still_gets_fusion_enthalpy(self):
        """Regression for slabx 1.0.5: pressure fixed, fusion not yet fixed."""

        class PressureOnlyBackend:
            def saturation_ratio(self, T):
                return (p_sublimation(min(T, T_TRIPLE)) / 101325.0)

            def d_saturation_ratio(self, T):
                h = 1e-3
                return ((self.saturation_ratio(T + h)
                         - self.saturation_ratio(T - h)) / (2 * h))

            def dh_vap(self, T):
                return 2_500_000.0

        stock = PressureOnlyBackend()
        assert correction_state(stock) == (True, False)
        fixed = with_sublimation(stock)
        assert fixed is not stock
        assert fixed.saturation_ratio(200.0) == stock.saturation_ratio(200.0)
        assert fixed.dh_vap(200.0) == pytest.approx(
            stock.dh_vap(200.0) + DH_FUSION)
        assert correction_state(fixed) == (True, True)


class TestUpstreamAdoption:
    """
    slabx 1.0.6 carries this correction upstream.

    Wrapping a backend that already has it would add the enthalpy of fusion
    twice -- 12 % on `dh_vap`, and **silently**, because the saturation ratio
    comes out identical either way. That is the kind of error this project
    has been bitten by before, so it is pinned.
    """

    def test_a_corrected_backend_is_not_wrapped_again(self):
        """Simulates an upstream backend by wrapping once, then again."""
        from slabx_lh2.water_ice import already_corrected
        once = with_sublimation(coolprop_water())
        assert already_corrected(once)
        assert with_sublimation(once) is once

    @needs_defect
    def test_a_clamped_backend_is_detected_as_needing_the_fix(self):
        """A clamped backend holds flat below the triple point."""
        from slabx_lh2.water_ice import already_corrected
        stock = coolprop_water()
        assert stock.saturation_ratio(200.0) == pytest.approx(
            stock.saturation_ratio(150.0), rel=1e-12)
        assert not already_corrected(stock)

    @needs_fix
    def test_the_upstream_fix_agrees_with_this_one(self):
        """
        Against slabx 1.0.6 and later: the values the upstream returns are
        the ones this module would have produced, and the wrapper stands
        aside.

        **This is the test that matters now.** If upstream ever diverges from
        IAPWS, or reintroduces the clamp, this catches it.
        """
        from slabx_lh2.water_ice import already_corrected
        stock = coolprop_water()
        assert already_corrected(stock)
        assert with_sublimation(stock) is stock
        for T in (270.0, 260.0, 240.0, 200.0):
            assert stock.saturation_ratio(T) * 101325.0 == pytest.approx(
                p_sublimation(T), rel=0.01)
        assert stock.dh_vap(200.0) - stock.dh_vap(280.0) == pytest.approx(
            DH_FUSION, rel=0.15), "the fusion enthalpy is not being added"

    @needs_fix
    def test_the_wrapper_is_a_no_op_and_therefore_harmless(self):
        """
        Calling code written for 1.0.4 keeps working on 1.0.6 unchanged, and
        does not double-count the fusion enthalpy.
        """
        stock = coolprop_water()
        w = with_sublimation(stock)
        for T in (200.0, 240.0, 280.0):
            assert w.saturation_ratio(T) == stock.saturation_ratio(T)
            assert w.dh_vap(T) == stock.dh_vap(T)

    def test_the_double_addition_it_prevents_is_real(self):
        """What would happen without the guard, so the size is on record."""
        from slabx_lh2.water_ice import DH_FUSION, SublimationWater
        once = with_sublimation(coolprop_water())
        twice = SublimationWater(once)          # bypassing the guard
        assert twice.dh_vap(200.0) == pytest.approx(
            once.dh_vap(200.0) + DH_FUSION)
        assert twice.dh_vap(200.0) / once.dh_vap(200.0) > 1.10

    def test_the_legacy_backend_is_corrected_not_mistaken_for_iapws(self):
        """
        Antoine extrapolation is neither a clamp nor IAPWS. Merely detecting
        that the curve is non-flat used to misclassify it as corrected.
        """
        legacy = water_backend()
        assert correction_state(legacy) == (False, False)
        ratio = legacy.saturation_ratio(200.0) * 101325.0 / p_sublimation(200.)
        assert 2.0 < ratio < 2.7
        fixed = with_sublimation(legacy)
        assert fixed is not legacy
        assert fixed.saturation_ratio(200.0) * 101325.0 == pytest.approx(
            p_sublimation(200.0), rel=0.01)
        assert correction_state(fixed) == (True, True)
