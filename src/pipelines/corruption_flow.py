from __future__ import annotations

from datetime import UTC, datetime

from core.config import load_settings
from core.utils import write_csv, write_json, write_text
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records

def main() -> None:
    """Run corruption and idempotent repair from the trusted raw snapshot.

    Repair intentionally re-reads ``crossref_records.json`` instead of editing
    the corrupted frame.  Re-running this command therefore produces the same
    repaired dataset and gives a reproducible lineage demonstration.
    """
    settings = load_settings()
    run_date = datetime.now(UTC)
    raw_records = load_raw_records(settings.paths.raw_records_json)
    baseline = build_clean_dataframe(raw_records, run_date)
    write_csv(baseline, settings.paths.clean_csv)
    baseline.to_json(settings.paths.clean_json, orient="records", indent=2, force_ascii=True)

    corrupted = corrupt_clean_dataframe(baseline, settings.paths.corruption_log)
    write_csv(corrupted, settings.paths.corrupted_clean_csv)
    corrupted.to_json(settings.paths.corrupted_clean_json, orient="records", indent=2, force_ascii=True)

    repaired = build_clean_dataframe(load_raw_records(settings.paths.raw_records_json), run_date)
    write_csv(repaired, settings.paths.repaired_clean_csv)
    repaired.to_json(settings.paths.repaired_clean_json, orient="records", indent=2, force_ascii=True)

    metrics = {
        "baseline": _metrics(baseline),
        "corrupted": _metrics(corrupted),
        "repaired": _metrics(repaired),
    }
    write_json(settings.paths.baseline_metrics, metrics["baseline"])
    write_json(settings.paths.corrupted_metrics, metrics["corrupted"])
    write_json(settings.paths.repaired_metrics, metrics["repaired"])
    write_text(settings.paths.comparison_report, _report(metrics))
    print("State       Rows  Unique IDs  Missing summaries  Duplicate IDs")
    for name, values in metrics.items():
        print(f"{name:<11} {values['rows']:<5} {values['unique_ids']:<11} {values['missing_summaries']:<18} {values['duplicate_ids']}")


def _metrics(df) -> dict[str, int]:
    return {
        "rows": int(len(df)),
        "unique_ids": int(df["paper_id"].nunique()) if "paper_id" in df else 0,
        "missing_summaries": int(df["summary"].fillna("").eq("").sum()) if "summary" in df else 0,
        "duplicate_ids": int(df["paper_id"].duplicated().sum()) if "paper_id" in df else 0,
    }


def _report(metrics: dict[str, dict[str, int]]) -> str:
    lines = [
        "# Corruption and Repair Report",
        "",
        "The repaired dataset is rebuilt from the trusted raw snapshot.",
        "",
        "| State | Rows | Unique IDs | Missing summaries | Duplicate IDs |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, values in metrics.items():
        lines.append(
            f"| {name.title()} | {values['rows']} | {values['unique_ids']} | "
            f"{values['missing_summaries']} | {values['duplicate_ids']} |"
        )
    lines.extend(["", "Repair is idempotent because it never uses the corrupted dataframe as its source."])
    return "\n".join(lines) + "\n"
