from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.utils import write_text


def _fmt(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).replace("|", "\\|").replace("\n", " ")


def _metric(metrics: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in metrics:
            return metrics[name]
    return None


def _status(value: Any) -> str:
    if value is None:
        return "N/A"
    return "PASS" if bool(value) else "FAIL"


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write the auditable baseline report in Markdown."""
    lines = [
        "# Phase 1 Baseline Report", "",
        "## Source summary", "",
        "| Field | Value |", "|---|---|",
    ]
    lines.extend(f"| {_fmt(key)} | {_fmt(value)} |" for key, value in source_summary.items())
    lines.extend([
        "", "## Evaluation metrics", "",
        "| Metric | Value |", "|---|---:|",
    ])
    lines.extend(f"| {_fmt(key)} | {_fmt(value)} |" for key, value in metrics.items())
    lines.extend([
        "", "## Data observability", "",
        "| Signal | Value |", "|---|---:|",
        f"| Quality gate | {_status(quality.get('success'))} |",
        f"| Expectations passed | {_fmt(quality.get('successful_expectations'))}/{_fmt(quality.get('evaluated_expectations'))} |",
        f"| Freshness SLA | {_status(freshness.get('is_fresh'))} |",
        f"| Stale rows | {_fmt(freshness.get('stale_rows'))}/{_fmt(freshness.get('total_rows'))} |",
        f"| Stale ratio | {_fmt(freshness.get('stale_ratio'))} |",
        f"| Latest publication | {_fmt(freshness.get('latest_published'))} |",
        f"| Oldest publication | {_fmt(freshness.get('oldest_published'))} |",
        "",
    ])
    write_text(Path(report_path), "\n".join(lines))


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
    baseline_quality: dict[str, Any] | None = None,
    baseline_freshness: dict[str, Any] | None = None,
) -> None:
    """Write a three-state comparison report for corruption and repair."""
    baseline_quality = baseline_quality or {}
    baseline_freshness = baseline_freshness or {}
    states = (baseline_metrics, corrupted_metrics, repaired_metrics)
    metric_rows = [
        ("Samples / rows", ("samples", "rows")),
        ("Retrieval hit rate", ("retrieval_hit_rate",)),
        ("Mean token F1", ("mean_token_f1",)),
        ("Judge accuracy", ("judge_accuracy",)),
        ("Mean judge score", ("mean_judge_score",)),
        ("Unique IDs", ("unique_ids",)),
        ("Missing summaries", ("missing_summaries",)),
        ("Duplicate IDs", ("duplicate_ids",)),
    ]
    lines = [
        "# Corruption and Repair Comparison", "",
        "The repaired state is compared with the clean baseline and intentionally corrupted data.", "",
        "## Metrics", "",
        "| Metric | Baseline | Corrupted | Repaired |",
        "|---|---:|---:|---:|",
    ]
    for label, keys in metric_rows:
        values = [_metric(state, *keys) for state in states]
        if any(value is not None for value in values):
            lines.append(f"| {label} | {_fmt(values[0])} | {_fmt(values[1])} | {_fmt(values[2])} |")

    lines.extend([
        "", "## Quality and freshness", "",
        "| Signal | Baseline | Corrupted | Repaired |",
        "|---|---:|---:|---:|",
        f"| Quality gate | {_status(baseline_quality.get('success'))} | {_status(corrupted_quality.get('success'))} | {_status(repaired_quality.get('success'))} |",
        f"| Freshness SLA | {_status(baseline_freshness.get('is_fresh'))} | {_status(corrupted_freshness.get('is_fresh'))} | {_status(repaired_freshness.get('is_fresh'))} |",
        f"| Stale rows | {_fmt(baseline_freshness.get('stale_rows'))} | {_fmt(corrupted_freshness.get('stale_rows'))} | {_fmt(repaired_freshness.get('stale_rows'))} |",
        f"| Stale ratio | {_fmt(baseline_freshness.get('stale_ratio'))} | {_fmt(corrupted_freshness.get('stale_ratio'))} | {_fmt(repaired_freshness.get('stale_ratio'))} |",
        "", "## Interpretation", "",
        "- Corrupted data is expected to fail one or more quality/freshness signals and degrade evaluation metrics.",
        "- Repair is successful when the repaired signals and metrics return to, or closely approach, the baseline.",
        "- Repair remains idempotent when it is rebuilt from the trusted raw snapshot rather than mutated corrupted data.",
        "",
    ])
    write_text(Path(report_path), "\n".join(lines))
