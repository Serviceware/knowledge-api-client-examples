#!/usr/bin/env python3
"""
Search texts and fetch the top hit's full content.

Demonstrates the typical "search to discover, fetch to read" pattern:
    1. POST /text/search        -- find candidate texts.
    2. GET  /text/{top-hit-id}  -- read the full content of the best match.

Requires:
    pip install requests

Usage:
    python search_and_fetch.py
"""

import sys
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Configuration -- replace placeholders with values for your environment.
# ---------------------------------------------------------------------------
BASE_URL = "https://<your-instance>/sabio-web/services"
USERNAME = "<username>"
PASSWORD = "<password>"

QUERY = "vacation policy"
LIMIT = 5


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


def search_texts(base_url: str, token: str, query: str, limit: int) -> dict[str, Any]:
    response = requests.post(
        f"{base_url}/text/search",
        json={
            "query": query,
            "limit": limit,
            "fields": ["id", "title", "score", "lastModified", "excerpt"],
        },
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "sabio-auth-token": token,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def find_text(base_url: str, token: str, text_id: str) -> dict[str, Any]:
    response = requests.get(
        f"{base_url}/text/{text_id}",
        params={"mode": "view"},
        headers={"sabio-auth-token": token},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    token = login(BASE_URL, USERNAME, PASSWORD)

    # 1. Search.
    search_payload = search_texts(BASE_URL, token, QUERY, LIMIT)
    data = search_payload.get("data", {})
    hits = data.get("result", []) or []

    print(f"Query: {QUERY!r} -- {data.get('total', 0)} total hit(s).")
    for index, hit in enumerate(hits, start=1):
        print(
            f"  {index:>2}. {hit.get('id')} "
            f"(score={hit.get('score')}): {hit.get('title')!r}"
        )

    if not hits:
        print("No hits -- nothing to fetch.")
        return 0

    # 2. Fetch the top hit.
    top_id = hits[0]["id"]
    print(f"\nFetching top hit {top_id}...")
    text_payload = find_text(BASE_URL, token, top_id)
    text = (text_payload.get("data") or {}).get("result") or {}

    print(f"Title:        {text.get('title')!r}")
    print(f"Tree path:    {text.get('treePath')}")
    print(f"Fragments:    {len(text.get('fragments', []) or [])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
