from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, normalize_whitespace, write_json


QUESTION_TYPES = ("summary", "authors", "date", "categories")
QUESTION_DISTRIBUTION = (
    "summary", "authors", "date", "categories", "summary",
    "authors", "date", "categories", "summary", "authors",
)


def _text(row: pd.Series, joined: str, raw: str) -> str:
    value = normalize_whitespace(str(row.get(joined, "")))
    if value:
        return value
    raw_value = row.get(raw, [])
    if isinstance(raw_value, (list, tuple, set)):
        return ", ".join(normalize_whitespace(str(item)) for item in raw_value if str(item).strip())
    return normalize_whitespace(str(raw_value))


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build a deterministic ten-question benchmark covering four task types."""
    required = {"paper_id", "title", "summary", "published"}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Cannot build test set; missing columns: {', '.join(missing)}")
    if len(df) < 4:
        raise ValueError("At least 4 documents are required to build a representative test set.")

    ordered = df.sort_values("paper_id", kind="stable").reset_index(drop=True)
    positions = [round(i * (len(ordered) - 1) / 9) for i in range(10)]
    test_set: list[dict[str, Any]] = []

    for index, (position, question_type) in enumerate(zip(positions, QUESTION_DISTRIBUTION), start=1):
        row = ordered.iloc[position]
        title = normalize_whitespace(str(row["title"]))
        paper_id = normalize_whitespace(str(row["paper_id"]))
        if question_type == "summary":
            question = f"What is the summary of the paper '{title}'?"
            answer = first_sentence(str(row["summary"]))
        elif question_type == "authors":
            question = f"Who are the authors of the paper '{title}'?"
            answer = _text(row, "authors_joined", "authors")
        elif question_type == "date":
            question = f"When was the paper '{title}' published?"
            parsed = pd.to_datetime(row["published"], errors="coerce")
            answer = parsed.date().isoformat() if not pd.isna(parsed) else ""
        else:
            question = f"What categories does the paper '{title}' belong to?"
            answer = _text(row, "categories_joined", "categories")

        if not paper_id or not title or not answer:
            raise ValueError(f"Document at row {position} lacks ground truth for {question_type}.")
        test_set.append(
            {
                "id": f"eval_{index:03d}",
                "question_type": question_type,
                "question": question,
                "ground_truth": answer,
                "ground_truth_doc_ids": [paper_id],
            }
        )

    write_json(Path(output_path), test_set)
    return test_set
