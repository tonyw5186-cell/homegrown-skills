#!/usr/bin/env python3
"""Read arXiv new submissions and HF Daily Papers heat as distinct feeds."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import json
import sys
import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ARXIV_URL = "https://rss.arxiv.org/rss/cs.AI+cs.LG+cs.CL"
ARXIV_API = "https://export.arxiv.org/api/query"
ARXIV_CATEGORIES = ("cs.AI", "cs.LG", "cs.CL")
ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"
HF_API = "https://huggingface.co/api/daily_papers"
MAX_BYTES = 2_000_000


def fetch(url: str, timeout: float, accept: str) -> tuple[bytes | None, str | None]:
    request = Request(url, headers={"User-Agent": "AgentSkills-paper-boards/1.0", "Accept": accept})
    try:
        with urlopen(request, timeout=min(max(timeout, 2.0), 30.0)) as response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                return None, "ValueError: response exceeds 2 MB safety limit"
            return body, None
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return None, f"{type(exc).__name__}: {exc}"[:500]


def parse_rss(body: bytes, cutoff: datetime, limit: int) -> list[dict]:
    root = ET.fromstring(body)
    channel = root.find("channel")
    rows = []
    seen: set[str] = set()
    for item in channel.findall("item") if channel is not None else []:
        values = {}
        for child in item:
            key = child.tag.rsplit("}", 1)[-1].split(":")[-1].lower()
            values[key] = child.text.strip() if child.text else ""
        announce = values.get("announce_type", "").strip().lower()
        raw_date = values.get("pubdate", "")
        try:
            published = parsedate_to_datetime(raw_date) if raw_date else None
            if published is not None and published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            if published is not None:
                published = published.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            published = None
        if announce and announce != "new":
            continue
        if published is None or published < cutoff:
            continue
        link = values.get("link", "")
        arxiv_id = link.rstrip("/").rsplit("/", 1)[-1] if link else ""
        if not arxiv_id or arxiv_id in seen:
            continue
        seen.add(arxiv_id)
        rows.append({"arxiv_id": arxiv_id, "title": values.get("title"), "authors": values.get("creator"), "published_at": published.isoformat(), "announce_type": announce or "unknown", "url": link})
    rows.sort(key=lambda row: row["published_at"], reverse=True)
    return rows[:limit]


def parse_atom(body: bytes, cutoff: datetime, limit: int) -> list[dict]:
    root = ET.fromstring(body)
    rows = []
    seen: set[str] = set()
    for entry in root.findall(ATOM_NS + "entry"):
        published_text = entry.findtext(ATOM_NS + "published", default="")
        try:
            published = datetime.fromisoformat(published_text.replace("Z", "+00:00")).astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            continue
        if published < cutoff:
            continue
        categories = [node.get("term", "") for node in entry.findall(ATOM_NS + "category")]
        if not set(categories).intersection(ARXIV_CATEGORIES):
            continue
        raw_id = entry.findtext(ATOM_NS + "id", default="").rstrip("/").rsplit("/", 1)[-1]
        arxiv_id = raw_id.split("v", 1)[0]
        if not arxiv_id or arxiv_id in seen:
            continue
        seen.add(arxiv_id)
        alternate = next((node.get("href") for node in entry.findall(ATOM_NS + "link") if node.get("rel") == "alternate"), None)
        rows.append({
            "arxiv_id": arxiv_id,
            "title": " ".join((entry.findtext(ATOM_NS + "title", default="").split())),
            "authors": [node.findtext(ATOM_NS + "name", default="") for node in entry.findall(ATOM_NS + "author")],
            "published_at": published.isoformat(),
            "updated_at": entry.findtext(ATOM_NS + "updated"),
            "announce_type": "unknown",
            "primary_category": (entry.find(ARXIV_NS + "primary_category").get("term") if entry.find(ARXIV_NS + "primary_category") is not None else None),
            "categories": categories,
            "url": alternate or ("https://arxiv.org/abs/" + raw_id if raw_id else None),
        })
    rows.sort(key=lambda row: row["published_at"], reverse=True)
    return rows[:limit]


def arxiv_items(days: int, limit: int, timeout: float) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rss_body, rss_error = fetch(ARXIV_URL, timeout, "application/rss+xml, application/xml, text/xml")
    rss_parse_error = None
    if rss_body is not None:
        try:
            rss_rows = parse_rss(rss_body, cutoff, limit)
            if rss_rows:
                return {"source": "arXiv RSS cs.AI+cs.LG+cs.CL", "status": "ok", "url": ARXIV_URL, "window_days": days, "filter": "announce_type=new; only items with a published date in window", "rows": rss_rows, "warning": "RSS is an announcement feed, not a quality ranking; missing announce_type is not verified as new."}
        except ET.ParseError as exc:
            rss_parse_error = f"XMLParseError: {exc}"[:500]

    params = {"search_query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL", "start": 0, "max_results": min(max(limit * 15, 30), 100), "sortBy": "submittedDate", "sortOrder": "descending"}
    atom_url = ARXIV_API + "?" + urlencode(params)
    atom_body, atom_error = fetch(atom_url, timeout, "application/atom+xml, application/xml")
    if atom_error or atom_body is None:
        return {"source": "arXiv", "status": "error", "url": atom_url, "error": atom_error, "rss_url": ARXIV_URL, "rss_error": rss_error or rss_parse_error or "RSS contained no in-window items", "rows": []}
    try:
        rows = parse_atom(atom_body, cutoff, limit)
    except ET.ParseError as exc:
        return {"source": "arXiv Atom API", "status": "error", "url": atom_url, "error": f"XMLParseError: {exc}"[:500], "rss_url": ARXIV_URL, "rows": []}
    rss_note = rss_error or rss_parse_error or "RSS contained no in-window items"
    return {"source": "arXiv Atom API (official fallback)", "status": "ok", "url": atom_url, "rss_url": ARXIV_URL, "rss_note": rss_note, "window_days": days, "filter": "published within window across cs.AI/cs.LG/cs.CL; announce_type unavailable in this API", "rows": rows, "warning": "Atom results are first-submission-date-window matches, not an exact announce_type=new feed; papers are not ranked by quality."}


def paper_rows(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("papers", "daily_papers", "data", "items", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


def get_field(obj: dict, *keys: str) -> object | None:
    for key in keys:
        if key in obj:
            return obj[key]
    return None


def hf_for_day(day: date, timeout: float, limit: int) -> tuple[str, list[dict], str | None]:
    url = HF_API + "?" + urlencode({"date": day.isoformat()})
    body, error = fetch(url, timeout, "application/json")
    if error or body is None:
        return day.isoformat(), [], error
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except json.JSONDecodeError as exc:
        return day.isoformat(), [], f"JSONDecodeError: {exc}"[:500]
    rows = []
    for item in paper_rows(data)[:limit]:
        paper = item.get("paper") if isinstance(item.get("paper"), dict) else item
        pid = get_field(paper, "id", "paper_id", "paperId") or get_field(item, "paper_id", "paperId")
        rows.append({"paper_id": pid, "title": get_field(paper, "title"), "upvotes": get_field(item, "upvotes", "likes") if get_field(item, "upvotes", "likes") is not None else get_field(paper, "upvotes", "likes"), "published_at": get_field(paper, "publishedAt", "published_at", "date") or day.isoformat(), "url": get_field(paper, "url") or ("https://huggingface.co/papers/" + str(pid) if pid else None)})
    return day.isoformat(), rows, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7, help="HF daily pages to request and arXiv feed window (1-14)")
    parser.add_argument("--limit", type=int, default=10, help="Maximum items per board (1-20)")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    if not 1 <= args.days <= 14 or not 1 <= args.limit <= 20:
        print(json.dumps({"status": "error", "error": "--days must be 1-14 and --limit 1-20"}))
        return 2

    now = datetime.now(timezone.utc)
    arxiv = arxiv_items(args.days, args.limit, args.timeout)
    dates = [now.date() - timedelta(days=i) for i in range(args.days)]
    hf_rows: list[dict] = []
    hf_errors = []
    with ThreadPoolExecutor(max_workers=min(4, args.days)) as pool:
        futures = [pool.submit(hf_for_day, day, args.timeout, args.limit) for day in dates]
        results = [future.result() for future in as_completed(futures)]
    seen: set[str] = set()
    for day, rows, error in sorted(results, key=lambda result: result[0], reverse=True):
        if error:
            hf_errors.append({"date": day, "error": error})
        for row in rows:
            key = str(row.get("paper_id") or row.get("url") or row.get("title"))
            if key not in seen:
                row["feed_date"] = day
                hf_rows.append(row)
                seen.add(key)
    hf_status = "ok" if hf_rows else "error"
    if hf_errors and hf_rows:
        hf_status = "partial"
    hf = {"source": "Hugging Face Daily Papers", "status": hf_status, "url": HF_API, "requested_days": args.days, "errors": hf_errors[:3], "rows": hf_rows[:args.limit], "warning": "Community discovery/upvotes are not scientific quality; failed dates are not replaced with search snippets."}
    boards = [arxiv, hf]
    status = "ok" if all(board["status"] == "ok" for board in boards) else "partial" if any(board["status"] != "error" for board in boards) else "error"
    result = {"status": status, "retrieved_at": now.isoformat(timespec="seconds"), "boards": boards}
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    return 0 if status != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
