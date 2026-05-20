#!/usr/bin/env python3
"""
Generate a grounded AI answer via the blocking POST /ai/answer endpoint.

Requires:
    pip install requests

Usage:
    python generate_answer.py
"""

import json
import re
import sys
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Configuration -- replace placeholders with values for your environment.
# ---------------------------------------------------------------------------
BASE_URL = "https://<your-instance>/sabio-web/services"
USERNAME = "<username>"
PASSWORD = "<password>"

# Stable identifier for your integration -- appears as the channel name in
# usage reports. Pick something unique to your integration.
CLIENT_NAME = "acme-portal"
CLIENT_VERSION = "1.0.0"

QUERY = "How do I reset my password?"

CITATION_RE = re.compile(r"\[ref:([^\]]+)\]")


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


def sabio_client_header() -> str:
    return json.dumps({"name": CLIENT_NAME, "version": CLIENT_VERSION})


def generate_answer(base_url: str, token: str, query: str) -> dict[str, Any]:
    response = requests.post(
        f"{base_url}/ai/answer",
        headers={
            "Content-Type": "application/json",
            "sabio-auth-token": token,
            "sabio-client": sabio_client_header(),
        },
        json={"query": query},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    token = login(BASE_URL, USERNAME, PASSWORD)
    payload = generate_answer(BASE_URL, token, QUERY)

    result = (payload.get("data") or {}).get("result") or {}
    answer = result.get("answer") or ""
    sources = result.get("sources") or []
    success = result.get("success")

    print(f"Question: {QUERY}\n")
    print("--- Answer ---")
    print(answer)
    print()

    cited_ids = set(CITATION_RE.findall(answer))
    print(f"--- Sources ({len(sources)} candidate, {len(cited_ids)} cited) ---")
    for source in sources:
        marker = "*" if source.get("id") in cited_ids else " "
        print(f"  {marker} {source.get('id')}  {source.get('resource')}  {source.get('title')}")
    print()
    print(f"success: {success}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
