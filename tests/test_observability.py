from __future__ import annotations

import json
from dataclasses import replace

import pandas as pd

from core.config import load_settings
from evaluation.testset import build_test_set
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report, generate_phase1_report


def _clean_frame() -> pd.DataFrame:
    settings = load_settings()
    return pd.read_json(settings.paths.clean_json)


def test_quality_gate_passes_clean_and_rejects_corruption(tmp_path) -> None:
    settings = load_settings()
    settings = replace(settings, paths=replace(settings.paths, quality_dir=tmp_path))
    clean = _clean_frame()
    assert run_data_quality_checks(clean, settings, "pytest_clean")["success"] is True

    corrupted = clean.copy()
    corrupted.loc[0, "summary"] = ""
    corrupted.loc[1, "paper_id"] = corrupted.loc[0, "paper_id"]
    result = run_data_quality_checks(corrupted, settings, "pytest_corrupted")
    assert result["success"] is False
    assert result["unsuccessful_expectations"] >= 2


def test_freshness_sla_boundary_and_missing_age(tmp_path) -> None:
    settings = load_settings()
    frame = _clean_frame().iloc[:4].copy()
    frame["age_days"] = [180, 181, 1, 2]
    report = build_freshness_report(frame, settings, tmp_path / "freshness.json")
    assert report["stale_rows"] == 1
    assert report["stale_ratio"] == 0.25
    assert report["is_fresh"] is True

    frame.loc[0, "age_days"] = None
    report = build_freshness_report(frame, settings, tmp_path / "freshness_missing.json")
    assert report["stale_rows"] == 2
    assert report["is_fresh"] is False


def test_testset_has_ten_questions_and_all_four_types(tmp_path) -> None:
    output = tmp_path / "test_set.json"
    test_set = build_test_set(_clean_frame(), output)
    assert len(test_set) == 10
    assert {item["question_type"] for item in test_set} == {
        "summary", "authors", "date", "categories"
    }
    assert len({item["id"] for item in test_set}) == 10
    assert json.loads(output.read_text(encoding="utf-8")) == test_set


def test_markdown_reports_include_expected_comparisons(tmp_path) -> None:
    quality = {"success": True, "successful_expectations": 6, "evaluated_expectations": 6}
    fresh = {"is_fresh": True, "stale_rows": 0, "total_rows": 24, "stale_ratio": 0.0}
    phase_path = tmp_path / "phase.md"
    comparison_path = tmp_path / "comparison.md"
    generate_phase1_report(phase_path, {"rows": 24}, {"retrieval_hit_rate": 1.0}, quality, fresh)
    generate_corruption_report(
        comparison_path,
        {"rows": 24, "retrieval_hit_rate": 1.0},
        {"rows": 24, "retrieval_hit_rate": 0.4},
        {"rows": 24, "retrieval_hit_rate": 1.0},
        {"success": False},
        quality,
        {"is_fresh": False, "stale_rows": 10, "stale_ratio": 0.42},
        fresh,
        quality,
        fresh,
    )
    assert "Data observability" in phase_path.read_text(encoding="utf-8")
    comparison = comparison_path.read_text(encoding="utf-8")
    assert "| Metric | Baseline | Corrupted | Repaired |" in comparison
    assert "| Quality gate | PASS | FAIL | PASS |" in comparison
