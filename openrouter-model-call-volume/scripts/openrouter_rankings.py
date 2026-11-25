#!/usr/bin/env python3
"""Read OpenRouter's server-rendered completed-week request ranking."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

URL = "https://openrouter.ai/rankings"
MAX_BYTES = 3_000_000


class Tables(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[dict] = []
        self.table: dict | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.caption: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.table = {"caption": "", "rows": []}
        elif tag == "caption" and self.table is not None:
            self.caption = []
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)
        if self.caption is not None:
            self.caption.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self.cell is not None:
            assert self.row is not None
            self.row.append(" ".join(" ".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            assert self.table is not None
            if self.row:
                self.table["rows"].append(self.row)
            self.row = None
        elif tag == "caption" and self.caption is not None:
            assert self.table is not None
            self.table["caption"] = " ".join(" ".join(self.caption).split())
            self.caption = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None


def fail(message: str, url: str = URL) -> dict:
    return {
        "source": "OpenRouter",
        "status": "error",
        "url": url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "error": message[:500],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=10, help="Maximum rows (1-20)")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()
    if not 1 <= args.limit <= 20:
        print(json.dumps(fail("--limit must be between 1 and 20"), ensure_ascii=True))
        return 2

    request = Request(URL, headers={"User-Agent": "AgentSkills-openrouter/1.0", "Accept": "text/html"})
    try:
        with urlopen(request, timeout=min(max(args.timeout, 2.0), 45.0)) as response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError("Response exceeds 3 MB safety limit")
            page = body.decode(response.headers.get_content_charset() or "utf-8", "replace")
        tables = Tables()
        tables.feed(page)
        target = next((t for t in tables.tables if "models ranked by requests in the most recent complete week" in t["caption"].lower()), None)
        if not target or len(target["rows"]) < 2:
            raise ValueError("Official page did not expose the completed-week request table; refusing to infer a ranking")
        headers = [h.strip().lower() for h in target["rows"][0]]
        rows = []
        for values in target["rows"][1:args.limit + 1]:
            record = {headers[i]: values[i] if i < len(values) else "" for i in range(len(headers))}
            rank_text = record.get("rank", "").strip()
            record["rank"] = int(rank_text) if rank_text.isdigit() else None
            record["row_type"] = "aggregate" if record.get("model", "").strip().lower() == "others" else "model"
            rows.append(record)
        result = {
            "source": "OpenRouter public rankings",
            "status": "ok",
            "url": URL,
            "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "metric": "requests",
            "time_window": target["caption"],
            "rows": rows,
        }
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        result = fail(f"{type(exc).__name__}: {exc}")
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
