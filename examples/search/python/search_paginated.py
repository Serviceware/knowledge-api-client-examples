#!/usr/bin/env python3
"""
Paginated iteration over search results.

Repeatedly calls POST /search with increasing 'start' offsets until all hits
have been retrieved or a configurable safety cap is reached.

Requires:
    pip install requests

Usage:
    python search_paginated.py
"""

import sys
from typing import Iterator

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "https://<your-instance>/sabio-web/services"
USERNAME = "<username>"
PASSWORD = "<password>"
QUERY = "*"
PAGE_SIZE = 50
MAX_PAGES = 100  # safety cap


def login(base_url: str, username: str, password: str) -> str:
    response = requests.post(
        f"{base_url}/authentication/credentials",
        json={"login": username, "key": password},
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30,
    )
    response.raise_for_status()
    token = response.json().get("data", {}).get("key")
    if not token:
        raise RuntimeError(f"Login failed: {response.text}")
    return token


def iter_hits(
    base_url: str,
    token: str,
    query: str,
    page_size: int,
    max_pages: int,
) -> Iterator[dict]:
    """Yield hits page by page until the result set is exhausted."""
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "sabio-auth-token": token,
    }

    start = 0
    page = 0
    total: int | None = None

    while page < max_pages:
        response = requests.post(
            f"{base_url}/search",
            json={
                "query": query,
                "start": start,
                "limit": page_size,
                "fields": ["id", "title", "resource"],
                "sort": [{"property": "id", "direction": "ASC"}],
            },
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json().get("data", {})

        if total is None:
            total = data.get("total", 0)

        hits = data.get("result", []) or []
        if not hits:
            return

        for hit in hits:
            yield hit

        start += len(hits)
        page += 1

        if total is not None and start >= total:
            return


def main() -> int:
    token = login(BASE_URL, USERNAME, PASSWORD)

    seen = 0
    for hit in iter_hits(BASE_URL, token, QUERY, PAGE_SIZE, MAX_PAGES):
        seen += 1
        print(f"{seen:>5}. [{hit.get('resource', '?')}] {hit.get('title', '')}")

    print(f"\nIterated over {seen} results.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
