from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import json
from pathlib import Path
import re
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import normalize_whitespace, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref ``message.items`` payload into normalized records.

    Pseudo-code:
    1. Duyet `payload["message"]["items"]`.
    2. Lay DOI, title, abstract, authors, subject, dates, URLs.
    3. Chuan hoa text va bo record khong hop le.
    4. Tra ve list `PaperRecord`.
    """
    items: Any = payload
    if isinstance(payload, dict):
        items = payload.get("message", {}).get("items", [])
    if not isinstance(items, list):
        return []

    records: list[PaperRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        paper_id = _clean_text(item.get("paper_id") or item.get("DOI"))
        title = _clean_text(_first(item.get("title")))
        published = _date_from_crossref(item.get("published") or item.get("issued"))
        if not paper_id or not title or not published:
            continue
        authors = _authors(item.get("authors") or item.get("author"))
        categories = _string_list(item.get("categories") or item.get("subject"))
        abs_url = _clean_text(item.get("abs_url") or item.get("URL"))
        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=_clean_text(item.get("summary") or item.get("abstract")),
                authors=authors,
                categories=categories,
                primary_category=_clean_text(item.get("primary_category")) or (categories[0] if categories else ""),
                published=published,
                updated=_date_from_crossref(item.get("updated")) or published,
                abs_url=abs_url,
                pdf_url=_clean_text(item.get("pdf_url")) or abs_url,
                comment=_clean_text(item.get("comment")) or f"Crossref record {paper_id}",
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch Crossref records and preserve both raw and normalized artifacts.

    Pseudo-code:
    1. Tao params tu `settings.source_query`, `settings.source_filter`, `settings.max_results`.
    2. Goi API voi retry cho cac status code nhu 429/503.
    3. Luu raw response vao `settings.paths.raw_api_response`.
    4. Parse payload bang `parse_crossref_payload`.
    5. Luu records vao `settings.paths.raw_records_json`.
    """
    snapshot = settings.paths.raw_api_response
    if not settings.refresh_source and snapshot.exists():
        return _load_snapshot(settings)

    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "select": "DOI,title,abstract,author,subject,published,issued,updated,URL,link",
    }
    payload: dict[str, Any] | None = None
    try:
        for attempt in range(3):
            response = requests.get("https://api.crossref.org/works", params=params, timeout=20)
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                time.sleep(2**attempt)
                continue
            response.raise_for_status()
            payload = response.json()
            break
    except (requests.RequestException, ValueError):
        if snapshot.exists():
            return _load_snapshot(settings)
        raise
    if payload is None:
        raise RuntimeError("Crossref returned no payload.")
    records = parse_crossref_payload(payload)
    write_json(snapshot, payload)
    write_json(settings.paths.raw_records_json, [record.__dict__ for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load a normalized records snapshot, or parse a raw Crossref payload."""
    return parse_crossref_payload(json.loads(path.read_text(encoding="utf-8")))


def _load_snapshot(settings: Settings) -> list[PaperRecord]:
    if settings.paths.raw_records_json.exists():
        return load_raw_records(settings.paths.raw_records_json)
    records = load_raw_records(settings.paths.raw_api_response)
    write_json(settings.paths.raw_records_json, [record.__dict__ for record in records])
    return records


def _clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return normalize_whitespace(unescape(re.sub(r"<[^>]+>", " ", text)))


def _first(value: Any) -> Any:
    return value[0] if isinstance(value, list) and value else value


def _string_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else ([value] if value else [])
    return list(dict.fromkeys(item for item in (_clean_text(entry) for entry in values) if item))


def _authors(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result = []
    for author in value:
        if isinstance(author, dict):
            name = normalize_whitespace(" ".join(filter(None, [str(author.get("given", "")), str(author.get("family", ""))])))
        else:
            name = _clean_text(author)
        if name:
            result.append(name)
    return list(dict.fromkeys(result))


def _date_from_crossref(value: Any) -> str:
    if isinstance(value, dict):
        parts = value.get("date-parts", [[]])
        parts = parts[0] if parts and isinstance(parts[0], list) else []
        if parts:
            return "-".join(f"{int(part):02d}" if index else str(int(part)) for index, part in enumerate(parts[:3]))
    return _clean_text(value)
