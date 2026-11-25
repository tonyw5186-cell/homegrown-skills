#!/usr/bin/env python3
"""Search GitHub's official API for AI repositories, not an official weekly trend score."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import ssl
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://api.github.com/search/repositories"
DEFAULT_QUERY = "topic:artificial-intelligence"
MAX_BYTES = 1_000_000
RELEASE_MAX_BYTES = 2_000_000
MAX_RELEASE_PAGES = 5


def _has_next_page(link_header: str) -> bool:
    return any('rel="next"' in part for part in link_header.split(","))


def release_asset_downloads(repo_name: str, timeout: float, context: ssl.SSLContext) -> dict:
    """Sum cumulative asset download counts across at most the latest 500 public releases."""
    releases_seen = 0
    assets_seen = 0
    downloads_total = 0
    prerelease_assets_seen = 0
    prerelease_downloads_total = 0
    stable_releases_seen = 0
    prerelease_releases_seen = 0
    pagination_complete = True
    error = None
    pages = 0
    headers = {"User-Agent": "AgentSkills-github-ai-projects/1.0", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

    for page in range(1, MAX_RELEASE_PAGES + 1):
        url = f"https://api.github.com/repos/{repo_name}/releases?per_page=100&page={page}"
        try:
            request = Request(url, headers=headers)
            with urlopen(request, timeout=min(max(timeout, 2.0), 30.0), context=context) as response:
                body = response.read(RELEASE_MAX_BYTES + 1)
                link_header = response.headers.get("Link", "")
            if len(body) > RELEASE_MAX_BYTES:
                raise ValueError("Release response exceeds 2 MB safety limit")
            payload = json.loads(body.decode("utf-8", "replace"))
            if not isinstance(payload, list):
                raise ValueError("GitHub releases response was not a list")
            pages += 1
            releases_seen += len(payload)
            for release in payload:
                if not isinstance(release, dict):
                    continue
                is_prerelease = bool(release.get("prerelease", False))
                if is_prerelease:
                    prerelease_releases_seen += 1
                else:
                    stable_releases_seen += 1
                assets = release.get("assets", [])
                if not isinstance(assets, list):
                    continue
                for asset in assets:
                    if not isinstance(asset, dict):
                        continue
                    count = asset.get("download_count")
                    if isinstance(count, int) and count >= 0:
                        assets_seen += 1
                        downloads_total += count
                        if is_prerelease:
                            prerelease_assets_seen += 1
                            prerelease_downloads_total += count
            if not _has_next_page(link_header):
                break
            if page == MAX_RELEASE_PAGES:
                pagination_complete = False
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            error = f"{type(exc).__name__}: {exc}"[:500]
            pagination_complete = False
            break

    if error and releases_seen:
        status = "partial"
    elif error:
        status = "error"
    elif pagination_complete:
        status = "ok"
    else:
        status = "partial"
    return {
        "repository": repo_name,
        "status": status,
        "release_asset_downloads_total": downloads_total if releases_seen or not error else None,
        "stable_release_asset_downloads_total": downloads_total - prerelease_downloads_total if releases_seen or not error else None,
        "prerelease_asset_downloads_total": prerelease_downloads_total if releases_seen or not error else None,
        "releases_scanned": releases_seen,
        "stable_releases_scanned": stable_releases_seen,
        "prerelease_releases_scanned": prerelease_releases_seen,
        "assets_counted": assets_seen,
        "stable_assets_counted": assets_seen - prerelease_assets_seen,
        "prerelease_assets_counted": prerelease_assets_seen,
        "pages_scanned": pages,
        "pagination_complete": pagination_complete,
        "scope": f"public release assets in up to {MAX_RELEASE_PAGES * 100} most recent releases; download_count is cumulative per asset",
        "error": error,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default=DEFAULT_QUERY, help="GitHub repository search query")
    parser.add_argument("--limit", type=int, default=10, help="Maximum repositories (1-30)")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--ca-file", default=os.environ.get("SSL_CERT_FILE"), help="Optional trusted PEM CA bundle; TLS verification remains enabled")
    parser.add_argument("--release-downloads", action="store_true", help="Also rank cumulative public GitHub Release asset downloads for the top 10 star candidates")
    args = parser.parse_args()
    captured = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if args.release_downloads and args.limit > 10:
        parser.error("--release-downloads is limited to --limit 10 to keep anonymous API usage bounded")
    if not 1 <= args.limit <= 30:
        print(json.dumps({"status": "error", "error": "--limit must be between 1 and 30", "retrieved_at": captured}))
        return 2

    query = urlencode({"q": args.query, "sort": "stars", "order": "desc", "per_page": args.limit})
    url = API + "?" + query
    request = Request(url, headers={"User-Agent": "AgentSkills-github-ai-projects/1.0", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    try:
        context = ssl.create_default_context(cafile=args.ca_file) if args.ca_file else ssl.create_default_context()
        with urlopen(request, timeout=min(max(args.timeout, 2.0), 30.0), context=context) as response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError("Response exceeds 1 MB safety limit")
            payload = json.loads(body.decode("utf-8", "replace"))
        items = payload.get("items", []) if isinstance(payload, dict) else []
        rows = []
        for rank, repo in enumerate(items[:args.limit], 1):
            if not isinstance(repo, dict):
                continue
            rows.append({"rank_by_cumulative_stars": rank, "repository": repo.get("full_name"), "description": repo.get("description"), "language": repo.get("language"), "stars_total": repo.get("stargazers_count"), "topics": repo.get("topics", []), "updated_at": repo.get("updated_at"), "pushed_at": repo.get("pushed_at"), "url": repo.get("html_url")})
        result = {"source": "GitHub REST Search API", "status": "ok", "url": url, "retrieved_at": captured, "query": args.query, "ordering": "cumulative stars; not weekly growth", "rows": rows}
        if args.release_downloads:
            stats = [release_asset_downloads(row["repository"], args.timeout, context) for row in rows if row.get("repository")]
            ranked = [stat for stat in stats if stat["status"] == "ok" and isinstance(stat["release_asset_downloads_total"], int)]
            ranked.sort(key=lambda stat: stat["release_asset_downloads_total"], reverse=True)
            result["release_asset_downloads_retrieved_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            result["release_asset_downloads_metric"] = "sum of cumulative download_count across public release assets; not clones, source archives, package downloads, or weekly growth"
            result["release_asset_download_ranking"] = [
                {"rank": rank, **stat} for rank, stat in enumerate(ranked, 1)
            ]
            result["release_asset_downloads_unranked"] = [
                stat for stat in stats if stat["status"] != "ok"
            ]
            result["release_asset_downloads_status"] = "ok" if len(ranked) == len(rows) else "partial"
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"source": "GitHub REST Search API", "status": "error", "url": url, "retrieved_at": captured, "query": args.query, "error": f"{type(exc).__name__}: {exc}"[:500]}
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
