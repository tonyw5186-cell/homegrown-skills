#!/usr/bin/env python3
"""Read the visible server-rendered skills.sh trending list and its own period label."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import unescape
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

URL = "https://www.skills.sh/trending?tab=trending"
MAX_BYTES = 2_000_000


def fail(error: str) -> dict:
    return {"source": "skills.sh", "status": "error", "url": URL, "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "error": error[:500], "rows": []}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=10, help="Maximum rows (1-20)")
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()
    if not 1 <= args.limit <= 20:
        print(json.dumps(fail("--limit must be between 1 and 20"), ensure_ascii=True))
        return 2

    request = Request(URL, headers={"User-Agent": "Mozilla/5.0 (compatible; AgentSkills-skills-sh/1.0)", "Accept": "text/html"})
    try:
        with urlopen(request, timeout=min(max(args.timeout, 2.0), 30.0)) as response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError("Response exceeds 2 MB safety limit")
            page = body.decode(response.headers.get_content_charset() or "utf-8", "replace")
        title_match = re.search(r"<title[^>]*>(.*?)</title>", page, re.I | re.S)
        title = unescape(re.sub(r"<[^>]+>", " ", title_match.group(1))).strip() if title_match else ""
        # The current Next.js HTML embeds the visible leaderboard objects in an escaped
        # initialSkills payload. If its schema changes, fail closed rather than guess.
        quote = r'\\?"'
        pattern = re.compile(quote + r"source" + quote + r"\s*:\s*" + quote + r'([^"\\]+)' + quote + r"\s*,\s*" + quote + r"skillId" + quote + r"\s*:\s*" + quote + r'([^"\\]+)' + quote + r"\s*,\s*" + quote + r"name" + quote + r"\s*:\s*" + quote + r'([^"\\]+)' + quote + r"\s*,\s*" + quote + r"installs" + quote + r"\s*:\s*(\d+)", re.S)
        matches = pattern.findall(page)
        if not matches:
            raise ValueError("No skills.sh leaderboard rows matched the expected server-rendered fields")
        rows = []
        seen = set()
        for rank, (source, skill_id, name, installs) in enumerate(matches, 1):
            key = (source, skill_id)
            if key in seen:
                continue
            seen.add(key)
            rows.append({"rank": rank, "skill": name, "source": source, "skill_id": skill_id, "installs": int(installs), "url": f"https://www.skills.sh/{source}/{skill_id}"})
            if len(rows) >= args.limit:
                break
        result = {"source": "skills.sh installation trend", "status": "ok", "url": URL, "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "period_label": title or "not exposed", "rows": rows}
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        result = fail(f"{type(exc).__name__}: {exc}")
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
