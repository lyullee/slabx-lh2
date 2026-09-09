"""Regression checks for claims corrected in the final release audit."""

from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "paper_results"


def _require(name: str) -> Path:
    path = PAPER / name
    if not path.exists():
        pytest.skip("private paper result is not distributed in the public package")
    return path


def test_frozen_results_include_the_measured_comparisons():
    d = json.loads(_require("results.json").read_text(encoding="utf-8"))
    assert d["measurements_installed"] is True
    assert d["lfl_in_bracket"] == 5
    assert 1.05 < d["safety_factor_required"] < 1.20
    assert d["negative_control_width_gate_lng"]["all_pass"] is True
    assert d["negative_control_width_gate_lng"]["max_change_pct"] == \
        pytest.approx(0.0, abs=1e-12)
    assert d["cross_fluid_water_effect_lng"]["max_change_pct"] > 10.0


def test_humidity_claims_are_kept_separate():
    d = json.loads(_require("humidity_sensitivity.json").read_text(
        encoding="utf-8"))
    assert d["horizontal_underprediction_at_every_rh"] is True
    assert d["orientation_separated_at_every_rh"] is False
    assert d["by_rh"]["100.0"]["separated"] is False
    assert d["by_rh"]["0.0"]["in_bracket"] == 3
    assert d["by_rh"]["75.0"]["in_bracket"] == 5


def test_polar_sensor_arc_is_not_used_as_a_fixed_x_cross_section():
    with _require("sensor_audit.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 30
    assert all(r["cross_section_mean_identifiable"] == "0" for r in rows)
    for trial, expected_min_span in (("4", 10.0), ("6", 19.0)):
        selected = [r for r in rows if r["trial"] == trial]
        xs = [float(r["x_downwind_m"]) for r in selected]
        assert max(xs) - min(xs) > expected_min_span
        assert all("not a common downwind plane" in r["note"]
                   for r in selected)


def test_entrainment_scenarios_are_neither_measurements_nor_bounds():
    with _require("entrainment_uncertainty.csv").open(
            encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert {r["scenario"] for r in rows} == {
        "half_peak_illustrative", "peak_equals_bulk_extreme"}
    assert "model_over_inferred_flux" in rows[0]
    text = " ".join(r["rationale"].lower() for r in rows)
    assert "lower bound" not in text
    assert "illustrative" in text and "extreme" in text


def test_negative_controls_and_cross_fluid_effect_are_distinct_outputs():
    with _require("negative_controls.csv").open(
            encoding="utf-8", newline="") as fh:
        controls = list(csv.DictReader(fh))
    assert controls
    assert all(r["pass_"] == "1" for r in controls)

    with _require("cross_fluid_water_effect.csv").open(
            encoding="utf-8", newline="") as fh:
        effects = list(csv.DictReader(fh))
    assert len(effects) == 10
    assert max(float(r["relative_change_pct"]) for r in effects) > 10.0
    assert all("no pass/fail" in r["interpretation"] for r in effects)


def test_public_builder_keeps_private_comparison_data_out(tmp_path):
    """The public allow-list must include model reproducers, not observations."""
    builder = ROOT / "scripts" / "make_public.py"
    if not builder.exists():
        pytest.skip("the public subset does not ship its private-tree builder")
    out = tmp_path / "slabx-lh2-public-audit"
    completed = subprocess.run(
        [sys.executable, str(builder), "--out", str(out)],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (out / "scripts" / "fit_critical_wind.py").exists()
    assert (out / "scripts" / "run_i9_benchmark.ps1").exists()
    assert not (out / "scripts" / "same_test_flacs.py").exists()
    assert not (out / "paper_results").exists()
    assert not list((out / "data").glob("lh2_*.csv"))
    assert not list(out.rglob("*.pyc"))
    assert (out / "README.md").read_bytes() == \
        (ROOT / "README_public.md").read_bytes()


def test_i9_runner_is_strict_and_self_validating():
    """The reference runner must reject other CPUs and audit every row group."""
    runner = ROOT / "scripts" / "run_i9_benchmark.ps1"
    text = runner.read_text(encoding="utf-8")
    assert 'i9-12900K' in text
    assert 'runtime_i9_0.1.3' in text
    assert 'validation.txt' in text
    for expected in (
        'ffi_test4|warm_e2e_single',
        'ffi_test6|warm_e2e_single',
        'nasa_test6|warm_e2e_single',
        'ffi6|warm_e2e_ffi6_batch',
        'all35|warm_e2e_35_sequential',
        'ffi_test4|cold_start_single',
    ):
        assert expected in text


def test_i9_013_raw_recomputes_the_archived_summary():
    root = PAPER / "runtime_i9_0.1.3"
    raw_path = root / "runtime_raw.csv"
    if not raw_path.exists():
        pytest.skip("private i9 repeat-level result is not distributed publicly")

    with raw_path.open(encoding="utf-8", newline="") as fh:
        raw = list(csv.DictReader(fh))
    with (root / "runtime_summary.csv").open(
            encoding="utf-8", newline="") as fh:
        summary = {
            (row["case_id"], row["metric"]): row for row in csv.DictReader(fh)
        }

    expected = {
        ("ffi_test4", "warm_e2e_single"): (100, 65.648925),
        ("ffi_test6", "warm_e2e_single"): (100, 117.070435),
        ("nasa_test6", "warm_e2e_single"): (100, 149.077435),
        ("ffi6", "warm_e2e_ffi6_batch"): (30, 444.90264),
        ("all35", "warm_e2e_35_sequential"): (30, 4196.8819),
        ("ffi_test4", "cold_start_single"): (20, 1526.25683),
    }
    assert len(raw) == 380
    assert not any(row["error"] for row in raw)
    assert {row["package_sha256"] for row in raw} == {"f02763515da7e4ac"}

    for key, (expected_n, expected_p95) in expected.items():
        values = sorted(float(row["elapsed_ms"]) for row in raw
                        if (row["case_id"], row["metric"]) == key)
        k = (len(values) - 1) * 0.95
        lo, hi = math.floor(k), math.ceil(k)
        p95 = values[lo] if lo == hi else (
            values[lo] + (values[hi] - values[lo]) * (k - lo)
        )
        assert len(values) == expected_n
        assert p95 == pytest.approx(expected_p95, abs=1e-9)
        assert float(summary[key]["p95_ms"]) == pytest.approx(p95, abs=1e-9)
