#!/usr/bin/env python3
"""
Faceted search example.

Issues an initial query that requests facets, prints the available filter
values per facet, then issues a follow-up query that narrows the result set
using one of those facet values as a filter.

Requires:
    pip install requests

Usage:
    python search_facets.py
"""

import sys

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "https://<your-instance>/sabio-web/services"
USERNAME = "<username>"
PASSWORD = "<password>"
QUERY = "vacation"
FACETS = ["resource", "language"]


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


def search(base_url: str, token: str, body: dict) -> dict:
    response = requests.post(
        f"{base_url}/search",
        json=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "sabio-auth-token": token,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def print_facets(payload: dict) -> None:
    facets = payload.get("data", {}).get("filter", []) or []
    if not facets:
        print("(no facets returned)")
        return
    for facet in facets:
        print(f"\nFacet: {facet.get('title')} (property={facet.get('property')})")
        for value in facet.get("values", []) or []:
            print(
                f"  - {value.get('title')} "
                f"(value={value.get('value')}, count={value.get('count')})"
            )


def main() -> int:
    token = login(BASE_URL, USERNAME, PASSWORD)

    # Step 1: initial search with facets requested.
    initial = search(
        BASE_URL,
        token,
        {
            "query": QUERY,
            "limit": 5,
            "facets": FACETS,
            "filterMode": "filtered",
        },
    )

    total = initial.get("data", {}).get("total", 0)
    print(f"Query: {QUERY!r} -- {total} total hits.")
    print_facets(initial)

    # Step 2: pick the first value of the first facet, then re-run with it
    # applied as a filter.
    facets = initial.get("data", {}).get("filter", []) or []
    if not facets or not facets[0].get("values"):
        print("\nNothing to drill into; exiting.")
        return 0

    facet = facets[0]
    chosen = facet["values"][0]
    print(
        f"\nNarrowing on {facet['property']} = {chosen['value']} "
        f"(expected {chosen.get('count')} hits)..."
    )

    narrowed = search(
        BASE_URL,
        token,
        {
            "query": QUERY,
            "limit": 5,
            "filters": [
                {"property": facet["property"], "values": [chosen["value"]]}
            ],
        },
    )

    narrowed_total = narrowed.get("data", {}).get("total", 0)
    print(f"Narrowed result: {narrowed_total} hits.")
    for hit in narrowed.get("data", {}).get("result", []) or []:
        print(f"  - [{hit.get('resource', '?')}] {hit.get('title', '<untitled>')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
