#!/usr/bin/env python3
"""
Fetch the relations of an entity from the Serviceware Knowledge REST API.

Authenticates with username/password, calls GET /relation/{type}/{id}, and
prints a compact summary grouped by relation type (attached / linked / embedded).

Requires:
    pip install requests

Usage:
    python get_relations.py
"""

import sys
from collections import defaultdict
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Configuration -- replace placeholders with values for your environment.
# ---------------------------------------------------------------------------
BASE_URL = "https://<your-instance>/sabio-web/services"
USERNAME = "<username>"
PASSWORD = "<password>"

# Entity to query relations for.
ENTITY_TYPE = "textelement"
ENTITY_ID = "<entity-id>"

# Set to True to only return relations originating from the entity.
BASE_ONLY = False


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


def get_relations(
    base_url: str,
    token: str,
    entity_type: str,
    entity_id: str,
    base_only: bool,
) -> dict[str, Any]:
    """Call GET /relation/{type}/{id}."""
    response = requests.get(
        f"{base_url}/relation/{entity_type}/{entity_id}",
        params={"baseOnly": "true" if base_only else "false"},
        headers={"sabio-auth-token": token},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def summarize(payload: dict[str, Any]) -> None:
    """Print a compact summary grouped by relation type."""
    data = payload.get("data", {})
    total = data.get("total", 0)
    relations = data.get("result", []) or []

    print(f"{total} total relation(s).")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for relation in relations:
        grouped[relation.get("relationType", "?")].append(relation)

    for relation_type in ("attached", "linked", "embedded"):
        bucket = grouped.get(relation_type, [])
        if not bucket:
            continue
        print(f"\n{relation_type.upper()} ({len(bucket)}):")
        for relation in bucket:
            details = relation.get("entityDetails", {}) or {}
            title = details.get("title") or "<no title / no permission>"
            extra_parts: list[str] = []
            if details.get("mimeType"):
                extra_parts.append(details["mimeType"])
            if details.get("size") is not None:
                extra_parts.append(f"{details['size']} bytes")
            if details.get("textId"):
                extra_parts.append(f"text={details['textId']}")
            if details.get("templateId"):
                extra_parts.append(f"template={details['templateId']}")
            extra = f" [{', '.join(extra_parts)}]" if extra_parts else ""
            print(
                f"  - {relation.get('entityType', '?')} "
                f"{relation.get('id')}: {title}{extra}"
            )


def main() -> int:
    token = login(BASE_URL, USERNAME, PASSWORD)
    payload = get_relations(BASE_URL, token, ENTITY_TYPE, ENTITY_ID, BASE_ONLY)
    summarize(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
