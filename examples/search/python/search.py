#!/usr/bin/env python3
"""
Basic search against the Serviceware Knowledge REST API.

Authenticates with username/password, then issues a single POST /search request
and prints the top hits.

Requires:
    pip install requests

Usage:
    python search.py
"""

import sys

import requests

# ---------------------------------------------------------------------------
# Configuration -- replace placeholders with values for your environment.
# ---------------------------------------------------------------------------
BASE_URL = "https://<your-instance>/sabio-web/services"
USERNAME = "<username>"
PASSWORD = "<password>"
QUERY = "vacation policy"
LIMIT = 10


def login(base_url: str, username: str, password: str) -> str:
    """Exchange credentials for a session token."""
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


def search(base_url: str, token: str, query: str, limit: int) -> dict:
    """Run a single search request."""
    response = requests.post(
        f"{base_url}/search",
        json={
            "query": query,
            "limit": limit,
            "fields": ["id", "title", "resource", "score", "lastModified", "excerpt"],
        },
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "sabio-auth-token": token,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    token = login(BASE_URL, USERNAME, PASSWORD)
    payload = search(BASE_URL, token, QUERY, LIMIT)

    data = payload.get("data", {})
    total = data.get("total", 0)
    hits = data.get("result", []) or []

    print(f"Query: {QUERY!r} -- {total} total hits, showing {len(hits)}.")
    for index, hit in enumerate(hits, start=1):
        print(
            f"  {index:>2}. [{hit.get('resource', '?')}] "
            f"{hit.get('title', '<untitled>')} "
            f"(score={hit.get('score')}, id={hit.get('id')})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
