from __future__ import annotations

import pandas as pd

from datetime import timedelta
from pathlib import Path

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Create a deterministic corrupted copy and record six corruption types.

    The input is never mutated.  The resulting frame is deliberately invalid
    for quality checks, while remaining readable so the impact of each defect
    can be demonstrated before rebuilding clean data from the raw snapshot.
    """
    corrupted = df.copy(deep=True)
    log: list[dict[str, object]] = []

    if len(corrupted) > 1:
        latest_index = corrupted["published"].idxmax()
        corrupted = corrupted.drop(index=latest_index)
    log.append({"type": "drop_latest_record", "count": int(len(df) - len(corrupted))})

    if not corrupted.empty:
        index = corrupted.index[0]
        corrupted.loc[index, "summary"] = ""
    log.append({"type": "blank_summary", "count": int(not corrupted.empty)})

    if not corrupted.empty:
        index = corrupted.index[0]
        corrupted.loc[index, "text_for_embedding"] = "CORRUPTED_NOISE ### " + str(
            corrupted.loc[index, "text_for_embedding"]
        )
    log.append({"type": "inject_text_noise", "count": int(not corrupted.empty)})

    if len(corrupted) > 1:
        index = corrupted.index[1]
        corrupted.loc[index, "title"] = str(corrupted.loc[index, "title"])[:12]
    log.append({"type": "truncate_title", "count": int(len(corrupted) > 1)})

    if len(corrupted) > 2:
        index = corrupted.index[2]
        published = pd.to_datetime(corrupted.loc[index, "published"])
        corrupted.loc[index, "published"] = (published - timedelta(days=3650)).date().isoformat()
    log.append({"type": "stale_published_date", "count": int(len(corrupted) > 2)})

    if not corrupted.empty:
        corrupted = pd.concat([corrupted, corrupted.iloc[[0]].copy()], ignore_index=True)
    log.append({"type": "duplicate_record", "count": int(not corrupted.empty)})

    for index, row in corrupted.iterrows():
        corrupted.loc[index, "text_for_embedding"] = _embedding_text(row)
    write_json(Path(output_log_path), {"corruptions": log})
    return corrupted.reset_index(drop=True)


def _embedding_text(row: pd.Series) -> str:
    return "\n".join(
        [
            f"Title: {row.get('title', '')}",
            f"Authors: {row.get('authors_joined', '')}",
            f"Published: {row.get('published', '')}",
            f"Categories: {row.get('categories_joined', '')}",
            f"Summary: {row.get('summary', '')}",
        ]
    )
