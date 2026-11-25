#!/usr/bin/env python3
"""Fetch separate Hugging Face and ModelScope model-trend rows."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HF_URL = "https://huggingface.co/api/models?sort=trendingScore&limit={limit}"
MS_URL = "https://modelscope.cn/api/v1/trend?Type=model"
MAX_BYTES = 2_000_000


def fetch_json(url: str, timeout: float) -> tuple[object | None, str | None]:
    request = Request(url, headers={"User-Agent": "AgentSkills-model-trends/1.0", "Accept": "application/json"})
    try:
        with urlopen(request, timeout=min(max(timeout, 2.0), 30.0)) as response:
            body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            return None, "response exceeds 2 MB limit"
        return json.loads(body.decode("utf-8", "replace")), None
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"[:500]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    if not 1 <= args.limit <= 20:
        print(json.dumps({"status": "error", "error": "--limit must be 1-20"}))
        return 2

    captured = datetime.now(timezone.utc).isoformat(timespec="seconds")
    hf_url = HF_URL.format(limit=args.limit)
    hf_data, hf_error = fetch_json(hf_url, args.timeout)
    ms_data, ms_error = fetch_json(MS_URL, args.timeout)

    hf_rows = []
    if isinstance(hf_data, list):
        for rank, row in enumerate(hf_data[:args.limit], 1):
            if isinstance(row, dict):
                model_id = row.get("id")
                hf_rows.append({
                    "rank": rank,
                    "model_id": model_id,
                    "trending_score": row.get("trendingScore"),
                    "downloads": row.get("downloads"),
                    "likes": row.get("likes"),
                    "last_modified": row.get("lastModified"),
                    "url": "https://huggingface.co/" + model_id if isinstance(model_id, str) else None,
                })
    elif hf_data is not None:
        hf_error = "unexpected Hub API response shape"

    ms_rows = []
    if isinstance(ms_data, dict):
        data = ms_data.get("Data")
        source_rows = data.get("Trends") if isinstance(data, dict) else None
        if isinstance(source_rows, list):
            for rank, row in enumerate(source_rows[:args.limit], 1):
                if isinstance(row, dict):
                    model_id = row.get("ResourceDisplay")
                    ms_rows.append({
                        "rank": rank,
                        "source_index": row.get("Index"),
                        "model_id": model_id,
                        "is_top": row.get("IsTop"),
                        "downloads": row.get("Downloads"),
                        "likes": row.get("Likes"),
                        "updated_at": row.get("GmtModified"),
                        "url": "https://modelscope.cn/models/" + model_id if isinstance(model_id, str) else None,
                    })
        else:
            ms_error = "unexpected ModelScope response shape"
    elif ms_data is not None:
        ms_error = "unexpected ModelScope response shape"

    boards = [
        {"source": "Hugging Face", "status": "ok" if hf_rows else "error", "url": hf_url, "rows": hf_rows, "error": hf_error},
        {"source": "ModelScope", "status": "ok" if ms_rows else "error", "url": MS_URL, "rows": ms_rows, "error": ms_error},
    ]
    states = [board["status"] for board in boards]
    status = "ok" if states == ["ok", "ok"] else "partial" if "ok" in states else "error"
    print(json.dumps({"status": status, "retrieved_at": captured, "boards": boards}, ensure_ascii=True, separators=(",", ":")))
    return 0 if status != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
