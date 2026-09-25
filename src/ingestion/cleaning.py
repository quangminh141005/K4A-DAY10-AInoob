from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from typing import Any, Mapping

import pandas as pd

from ingestion.crossref import PaperRecord
from core.utils import normalize_whitespace


def build_clean_dataframe(records: list[PaperRecord] | pd.DataFrame, run_date: datetime | date) -> pd.DataFrame:
   """Build a clean DataFrame ready for quality checks and embedding.

    Pseudo-code:
    1. Normalize title, summary, authors, categories.
    2. Parse published/updated date.
    3. Tinh age_days.
    4. Tao cot helper:
       - authors_joined
       - categories_joined
       - summary_chars
       - text_for_embedding
    5. Drop duplicates va filter row xau.
    6. Sort dataframe va return.
    """
   rows = records.to_dict(orient="records") if isinstance(records, pd.DataFrame) else [
      asdict(record) if is_dataclass(record) else dict(record) for record in records
   ]
   run_day = run_date.date() if isinstance(run_date, datetime) else run_date
   cleaned: list[dict[str, Any]] = []
   seen_ids: set[str] = set()
   for row in rows:
      paper_id = normalize_whitespace(str(row.get("paper_id", "")))
      title = normalize_whitespace(str(row.get("title", "")))
      published = pd.to_datetime(row.get("published"), errors="coerce")
      if not paper_id or not title or pd.isna(published) or paper_id in seen_ids:
         continue
      seen_ids.add(paper_id)
      published_day = published.date()
      authors = _clean_list(row.get("authors"))
      categories = _clean_list(row.get("categories"))
      summary = normalize_whitespace(str(row.get("summary", "")))
      normalized = dict(row)
      normalized.update({
         "paper_id": paper_id,
         "title": title,
         "summary": summary,
         "authors": authors,
         "categories": categories,
         "published": published_day.isoformat(),
         "updated": _clean_date(row.get("updated"), published_day),
         "authors_joined": ", ".join(authors),
         "categories_joined": ", ".join(categories),
         "summary_chars": len(summary),
         "age_days": (run_day - published_day).days,
      })
      normalized["text_for_embedding"] = _embedding_text(normalized)
      cleaned.append(normalized)
   return pd.DataFrame(cleaned).sort_values("paper_id").reset_index(drop=True) if cleaned else pd.DataFrame()


def _clean_list(value: Any) -> list[str]:
   values = value if isinstance(value, (list, tuple, set)) else ([value] if value else [])
   return list(dict.fromkeys(normalize_whitespace(str(item)) for item in values if normalize_whitespace(str(item))))


def _clean_date(value: Any, fallback: date) -> str:
   parsed = pd.to_datetime(value, errors="coerce")
   return fallback.isoformat() if pd.isna(parsed) else parsed.date().isoformat()


def _embedding_text(row: Mapping[str, Any]) -> str:
   return "\n".join([
      f"Title: {row['title']}",
      f"Authors: {row['authors_joined']}",
      f"Published: {row['published']}",
      f"Categories: {row['categories_joined']}",
      f"Summary: {row['summary']}",
   ])
