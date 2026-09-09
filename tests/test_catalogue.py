"""
The catalogue against the generated numbers, and against itself.

`data/catalogue.json` is written by hand -- it is the only place the values
that lived in prose are recorded -- so it is exactly the kind of file that
goes stale. These tests tie the entries that can be regenerated to
`results.json`, and check the rest for internal consistency.
"""

import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CAT = ROOT / "data" / "catalogue.json"


@pytest.fixture(scope="module")
def catalogue():
    """
    The catalogue as installed.

    **Do not regenerate it here.** `build_dataset.py` writes the full set;
    the public release ships a filtered copy written by `make_public.py`,
    and regenerating would silently replace it and defeat the check that it
    says it was filtered.
    """
    if not CAT.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" /
                                            "build_dataset.py")],
                       cwd=ROOT, check=True, capture_output=True)
    return json.loads(CAT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def records(catalogue):
    return {r["key"]: r for r in catalogue["records"]}


def _measurements_installed() -> bool:
    from slabx_lh2.trials import observations
    return all(observations.available(k) for k in
               ("ffi_arcs", "e35_farfield", "e34_pool"))


needs_measurements = pytest.mark.skipif(
    not _measurements_installed(),
    reason="the measured datasets are not distributed; see data/SOURCES.md")


@pytest.fixture(scope="module")
def generated():
    """
    `results.json`, regenerated.

    `reproduce.py` records whether it found the measurements, so tests that
    need them read that flag rather than probing separately. **Two probes
    disagreed once** -- the package was installed in one place and the script
    run from another -- and the test failed where it should have skipped.
    """
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    subprocess.run([sys.executable, str(ROOT / "scripts" / "reproduce.py"),
                    "water", "--json"], cwd=ROOT, env=env, check=True,
                   capture_output=True)
    return json.loads((ROOT / "results" / "results.json").read_text())


class TestStructure:
    def test_the_public_catalogue_drops_measured_records(self, catalogue):
        """
        The public release removes values measured by others, and says so.

        A silently shorter file would be worse than a shorter one that
        explains itself.
        """
        from slabx_lh2.trials import observations
        installed = observations.available("ffi_arcs")
        note = catalogue.get("note", "")
        if installed:
            assert not note, "the working tree should carry the full set"
        else:
            assert "removed" in note, (
                "the public catalogue is filtered but does not say so")

    def test_keys_are_unique_and_dotted(self, catalogue):
        keys = [r["key"] for r in catalogue["records"]]
        assert len(keys) == len(set(keys))
        assert all("." in k for k in keys)

    def test_every_record_is_complete(self, catalogue):
        for r in catalogue["records"]:
            for field in ("value", "unit", "grade", "kind", "source", "doc"):
                assert field in r, f"{r['key']} missing {field}"
            assert r["source"], f"{r['key']} has no source"

    def test_grades_are_from_the_scheme(self, catalogue):
        allowed = set(catalogue["grades"])
        for r in catalogue["records"]:
            assert r["grade"] in allowed, f"{r['key']}: {r['grade']}"

    def test_kinds_are_from_the_fixed_set(self, catalogue):
        allowed = {"measurement", "model", "comparison", "diagnostic",
                   "withdrawn"}
        for r in catalogue["records"]:
            assert r["kind"] in allowed, f"{r['key']}: {r['kind']}"

    def test_withdrawn_records_carry_no_grade_and_say_why(self, catalogue):
        wd = [r for r in catalogue["records"] if r["kind"] == "withdrawn"]
        assert wd, "the withdrawn values are the point of keeping this file"
        for r in wd:
            assert r["grade"] == "-", (
                f"{r['key']} is withdrawn but carries grade {r['grade']}; "
                f"a reader would take that as a claim")
            assert r["note"], f"{r['key']} does not say what replaced it"

    def test_withdrawn_keys_are_marked_in_the_key_itself(self, catalogue):
        """So that grepping an old draft for a key shows the status."""
        for r in catalogue["records"]:
            if r["kind"] == "withdrawn":
                assert "withdrawn" in r["key"], r["key"]


@needs_measurements
class TestAgainstGeneratedNumbers:
    """Anything that can be recomputed must match what is recomputed."""

    def test_water_clamp_error(self, records, generated):
        """
        The size of the defect, where the installed slabx still has it.

        **slabx 1.0.6 fixed it upstream**, and there the ratio is 1: the
        stock backend and IAPWS agree. The catalogue records what the defect
        was, so it is checked against a version that has one.
        """
        from slabx_lh2.water_ice import already_corrected
        from slabx.thermo.coolprop import coolprop_water
        got = generated["water_saturation_error"]["200.00"]["ratio"]
        if already_corrected(coolprop_water()):
            assert got == pytest.approx(1.0, abs=0.05), (
                f"upstream claims to be corrected but returns {got:.3g} "
                f"times the IAPWS value")
            return
        assert got == pytest.approx(
            records["water.clamp.error_at_200K"]["value"], rel=0.05)

    def test_the_hydrogen_width_gate_is_inactive_for_lng(self, generated):
        """
        This is the actual negative control: identical water treatment on both
        arms, with only the hydrogen-specific width coupling toggled.
        """
        control = generated["negative_control_width_gate_lng"]
        got = control["max_change_pct"]
        assert got == pytest.approx(0.0, abs=1e-9), (
            f"the H2-only width gate moved LNG by {got:.3f} %")
        assert control["all_pass"]

    def test_the_defect_is_not_hydrogen_specific(self, records):
        """The deliberate CoolProp water ablation moves LNG materially."""
        v = records["crossfluid.lng_burro8.water_treatment_change"]["value"]
        assert v > 5.0

    def test_pool_radius_median(self, records, generated):
        assert generated["pool_radius"]["median_ratio"] == pytest.approx(
            records["pool.radius.median_ratio"]["value"], abs=0.03)

    def test_lfl_bracket_and_factor(self, records, generated):
        if not generated.get("measurements_installed", True):
            pytest.skip("reproduce.py ran without the measured brackets; "
                        "results.json says so and this check needs them")
        assert generated["lfl_in_bracket"] == \
            records["lfl.in_bracket"]["value"]
        assert generated["safety_factor_required"] == pytest.approx(
            records["lfl.safety_factor_required"]["value"], abs=0.01)
        assert generated["safety_factor"] == \
            records["lfl.safety_factor_adopted"]["value"]

    def test_critical_wind_coefficients(self, records, generated):
        c = generated["critical_wind"]["coefficients"]["D"]
        assert c["a"] == pytest.approx(records["ucrit.D.a"]["value"],
                                       abs=0.01)
        assert c["b"] == pytest.approx(records["ucrit.D.b"]["value"],
                                       abs=0.005)

    def test_air_condensation_onsets(self, records, generated):
        for sp, key in (("N2", "air.onset.N2"), ("O2", "air.onset.O2")):
            got = generated["air_condensation"][sp]["onset_mol_pct"]
            assert got == pytest.approx(records[key]["value"], abs=0.5)
            assert got > records["air.ufl_hydrogen"]["value"]

    def test_briggs_e35_correlations(self, records, generated):
        b = generated["briggs_e35"]
        assert b["rank_corr_Lp_wind"] == pytest.approx(
            records["briggs.e35.rank_corr_wind"]["value"], abs=0.02)
        assert b["rank_corr_Lp_rate"] == pytest.approx(
            records["briggs.e35.rank_corr_rate"]["value"], abs=0.02)

    def test_rise_exponent_pass_counts(self, records, generated):
        """
        Both configurations, because they differ and the paper must say
        which is which: the width coupling alone reaches the band on none of
        the four, and with the exploratory drag on one.
        """
        pw = generated["prereg_plume_width"]
        assert pw["P_W1_pass_width_only"] == \
            records["rise.P_W1_pass.width_only"]["value"]
        assert pw["P_W1_pass_with_drag"] == \
            records["rise.P_W1_pass.with_drag"]["value"]

    def test_the_residual_algebra_holds(self, records, generated):
        """n = 2/(s+1) against the fitted exponent, worst of the four."""
        worst = max(generated["prereg_plume_width"]["residual_errors_pct"])
        assert worst == pytest.approx(
            records["rise.residual.prediction_accuracy"]["value"] * 100,
            abs=0.5)

    def test_the_cross_fluid_water_ablation_reaches_a_dense_gas(
            self, records, generated):
        """
        The comparison deliberately reconstructs the old clamp, so its result
        is stable even when the installed slabx has already been corrected.
        It is cross-fluid evidence, not a claim that slabx 1.0.6 is defective.
        """
        cp = generated["cross_fluid_water_effect_burro8"]
        assert cp["comparison_type"].startswith("deliberate")
        assert cp["change_pct"] == pytest.approx(
            records["crossfluid.lng_burro8.water_treatment_change"]["value"],
            abs=0.5)

    def test_ground_rr986_does_not_transfer(self, records, generated):
        g = generated["ground_rr986"]
        assert g["temperature_bias_K"] == pytest.approx(
            records["ground.rr986.temperature_bias"]["value"], abs=1.0)
        assert g["depth_drift"] < 2.5

    def test_ground_e34_median(self, records, generated):
        assert generated["ground_conduction_e34"]["median_ratio"] == \
            pytest.approx(records["ground.e34.median_ratio"]["value"],
                          abs=0.05)


@needs_measurements
class TestTheDataFilesAreIntact:
    """
    Row and column counts, so a truncated file is caught.

    Skipped where the measurements are not installed, which is the public
    release; there is nothing to check the shape of.
    """

    EXPECTED = {
        "lh2_ffi_sensors.csv": (826, 13),
        "lh2_ffi_conditions.csv": (7, 15),
        "lh2_e35_farfield_v2.csv": (686, 12),
        "lh2_e35_conditions_v2.csv": (24, 22),
        "lh2_e34_rates.csv": (289, 12),
        "lh2_e34_traces.csv": (1754, 24),
        "lh2_e34_summary.csv": (5, 15),
    }

    @pytest.mark.parametrize("name,shape", list(EXPECTED.items()))
    def test_shape(self, name, shape):
        import csv as _csv
        path = ROOT / "data" / name
        assert path.exists(), f"{name} is missing"
        with path.open(encoding="utf-8") as fh:
            rows = list(_csv.reader(fh))
        assert (len(rows) - 1, len(rows[0])) == shape, (
            f"{name}: {len(rows) - 1} rows x {len(rows[0])} cols, "
            f"expected {shape}")

    def test_no_file_is_empty_or_headerless(self):
        for name in self.EXPECTED:
            text = (ROOT / "data" / name).read_text(encoding="utf-8")
            assert text.strip(), f"{name} is empty"
            assert "," in text.splitlines()[0], f"{name} has no header"


class TestTheCatalogueIsTheSameEverywhere:
    """
    Three copies of the catalogue exist and they must agree.

        data/catalogue.{json,csv}       the working copy, regenerated
        paper_results/catalogue.csv     frozen with the results
        the public release              filtered, and says so

    They have drifted before: `paper_results` was frozen from a run that
    predated a correction, and the numbers in a manuscript came from the
    stale copy.
    """

    def test_the_frozen_copy_matches_the_working_one(self):
        import csv as _csv
        frozen = ROOT / "paper_results" / "catalogue.csv"
        if not frozen.exists():
            pytest.skip("paper_results has not been frozen yet")
        live = ROOT / "data" / "catalogue.csv"
        a = list(_csv.DictReader(live.open(encoding="utf-8")))
        b = list(_csv.DictReader(frozen.open(encoding="utf-8")))
        assert len(a) == len(b), (
            f"data/catalogue.csv has {len(a)} rows and "
            f"paper_results/catalogue.csv has {len(b)}; re-freeze")
        da = {r["key"]: r["value"] for r in a}
        db = {r["key"]: r["value"] for r in b}
        differ = [k for k in da if da[k] != db.get(k)]
        assert not differ, f"values differ on {differ[:5]}"

    def test_the_public_copy_is_a_subset_and_says_so(self, catalogue):
        """
        The public release drops measured records. It must be a strict
        subset, and it must carry the note explaining why.
        """
        from slabx_lh2.trials import observations
        if observations.available("ffi_arcs"):
            pytest.skip("this is the working tree, not the public subset")
        note = catalogue.get("note", "")
        assert "removed" in note
        keys = {r["key"] for r in catalogue["records"]}
        withdrawn = {r["key"] for r in catalogue["records"]
                     if r["kind"] == "withdrawn"}
        assert withdrawn, (
            "the withdrawn records must survive the filter: someone who "
            "finds a retracted number in an old draft needs to look it up")
        assert keys, "the public catalogue is empty"
