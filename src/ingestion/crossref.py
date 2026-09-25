from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Any

from core.config import Settings


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


class _HTMLTextExtractor(HTMLParser):
    """Collect text from Crossref's JATS/XML-like abstract markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    parser = _HTMLTextExtractor()
    try:
        parser.feed(str(value))
        text = " ".join(parser.parts)
    except (TypeError, ValueError):
        text = re.sub(r"<[^>]+>", " ", str(value))
    return " ".join(unescape(text).split())


def _first_text(value: Any) -> str:
    if isinstance(value, list):
        return _clean_text(value[0]) if value else ""
    return _clean_text(value)


def _date_string(value: Any) -> str:
    """Return a Crossref date object or ISO timestamp as YYYY-MM-DD."""
    if isinstance(value, dict):
        parts = value.get("date-parts")
        if isinstance(parts, list) and parts and isinstance(parts[0], list):
            numbers = parts[0]
            try:
                year = int(numbers[0])
                month = int(numbers[1]) if len(numbers) > 1 else 1
                day = int(numbers[2]) if len(numbers) > 2 else 1
                return date(year, month, day).isoformat()
            except (IndexError, TypeError, ValueError):
                pass
        value = value.get("date-time") or value.get("timestamp")

    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value / 1000).date().isoformat()
        except (OSError, OverflowError, ValueError):
            return ""
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", value.strip())
            return match.group(0) if match else ""
    return ""


def _first_date(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        parsed = _date_string(item.get(key))
        if parsed:
            return parsed
    return ""


def _author_name(author: Any) -> str:
    if not isinstance(author, dict):
        return _clean_text(author)
    name = _clean_text(author.get("name"))
    if name:
        return name
    return " ".join(
        part for part in (_clean_text(author.get("given")), _clean_text(author.get("family"))) if part
    )


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Convert a Crossref API response into normalized paper records.

    Records without a DOI or title are ignored. Missing optional fields become
    empty strings/lists instead of making the entire response fail.
    """
    if not isinstance(payload, dict):
        return []
    message = payload.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("items"), list):
        return []

    records: list[PaperRecord] = []
    for item in message["items"]:
        if not isinstance(item, dict):
            continue

        doi = _clean_text(item.get("DOI"))
        doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE).strip()
        title = _first_text(item.get("title"))
        if not doi or not title:
            continue

        raw_authors = item.get("author", [])
        if not isinstance(raw_authors, list):
            raw_authors = [raw_authors]
        authors = [name for author in raw_authors if (name := _author_name(author))]

        subjects = item.get("subject", [])
        if not isinstance(subjects, list):
            subjects = [subjects]
        categories = [category for value in subjects if (category := _clean_text(value))]

        published = _first_date(item, "published", "published-print", "published-online", "issued", "created")
        updated = _first_date(item, "updated", "indexed", "deposited", "created") or published
        abs_url = _clean_text(item.get("URL")) or f"https://doi.org/{doi}"

        pdf_url = ""
        links = item.get("link", [])
        if isinstance(links, list):
            for link in links:
                if not isinstance(link, dict):
                    continue
                content_type = str(link.get("content-type", "")).lower()
                candidate = _clean_text(link.get("URL"))
                if candidate and ("pdf" in content_type or candidate.lower().endswith(".pdf")):
                    pdf_url = candidate
                    break

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=_clean_text(item.get("abstract")),
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "",
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url or abs_url,
                comment=f"Crossref record {doi}",
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """TODO(student): goi source API, luu raw response, parse thanh records.

    Pseudo-code:
    1. Tao params tu `settings.source_query`, `settings.source_filter`, `settings.max_results`.
    2. Goi API voi retry cho cac status code nhu 429/503.
    3. Luu raw response vao `settings.paths.raw_api_response`.
    4. Parse payload bang `parse_crossref_payload`.
    5. Luu records vao `settings.paths.raw_records_json`.
    """
    raw_respond_path = settings.paths.raw_api_response
    raw_records_path = settings.paths.raw_records_json

    payload: dict | None = None

    if not settings.refresh_source and raw_records_path.exists():
        payload = json.loads(raw_respond_path.read_text(encoding="utf-8"))
    else:
        retry_policy = Retry( # handle when api don't respond 
            total=4,
            connect=4,
            read=4,
            status=4,
            backoff_factor=4,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
        )

        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=retry_policy))

        params = {
            "query": settings.source_query,
            "filter": settings.source_filter,
            "rows": settings.max_results,
        }

        headers = {
            "Accept": "application/json",
            "User-Agent": "day10-data-observability-lab/1.0"
        }

        

def load_raw_records(path: Path) -> list[PaperRecord]:
    """TODO(student): doc JSON snapshot va map thanh `PaperRecord`."""
    raise NotImplementedError("Student task: implement raw record loading.")
