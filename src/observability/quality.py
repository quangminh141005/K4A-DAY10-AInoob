from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def _quality_report_path(settings: Settings, report_name: str) -> Path:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", report_name).strip("_").lower() or "quality"
    return settings.paths.quality_dir / f"{slug}_quality_report.json"


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Validate a paper dataframe with the Great Expectations 1.x fluent API."""
    try:
        import great_expectations as gx
        from great_expectations import expectations as gxe
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Great Expectations is required for quality checks; install project dependencies first."
        ) from exc

    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    expectations = [
        gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000),
        gxe.ExpectColumnValuesToNotBeNull(column="paper_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="title"),
        gxe.ExpectColumnValuesToNotBeNull(column="text_for_embedding"),
        gxe.ExpectColumnValuesToBeUnique(column="paper_id"),
        gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30),
    ]

    checks: list[dict[str, Any]] = []
    for expectation in expectations:
        raw = batch.validate(expectation).to_json_dict()
        config = raw.get("expectation_config", {})
        checks.append(
            {
                "expectation_type": config.get("type", expectation.__class__.__name__),
                "kwargs": config.get("kwargs", {}),
                "success": bool(raw.get("success", False)),
                "result": raw.get("result", {}),
                "exception_info": raw.get("exception_info", {}),
            }
        )

    successful = sum(check["success"] for check in checks)
    payload: dict[str, Any] = {
        "report_name": report_name,
        "success": successful == len(checks),
        "row_count": int(len(df)),
        "evaluated_expectations": len(checks),
        "successful_expectations": successful,
        "unsuccessful_expectations": len(checks) - successful,
        "checks": checks,
    }
    write_json(_quality_report_path(settings, report_name), payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Evaluate the <=25% stale-row SLA and persist its JSON artifact."""
    threshold = int(settings.freshness_threshold_days)
    total_rows = int(len(df))
    ages = pd.to_numeric(df.get("age_days", pd.Series(index=df.index, dtype=float)), errors="coerce")
    stale_mask = ages.isna() | ages.gt(threshold)
    stale_rows = int(stale_mask.sum())
    stale_ratio = stale_rows / total_rows if total_rows else 1.0

    published = pd.to_datetime(
        df.get("published", pd.Series(index=df.index, dtype="object")), errors="coerce"
    ).dropna()
    payload: dict[str, Any] = {
        "latest_published": published.max().date().isoformat() if not published.empty else None,
        "oldest_published": published.min().date().isoformat() if not published.empty else None,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": round(stale_ratio, 6),
        "freshness_threshold_days": threshold,
        "max_stale_ratio": 0.25,
        "is_fresh": total_rows > 0 and stale_ratio <= 0.25,
    }
    write_json(Path(report_path), payload)
    return payload
