#!/usr/bin/env python3
"""
Fetch a single text by ID from the Serviceware Knowledge REST API.

Authenticates with username/password, calls GET /text/{id}, and prints
title, tree path, validity window, and a per-fragment summary.

Requires:
    pip install requests

Usage:
    python find_text.py
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

TEXT_ID = "<text-id>"
MODE = "view"   # "view" or "edit"


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


def find_text(base_url: str, token: str, text_id: str, mode: str) -> dict[str, Any]:
    """Call GET /text/{id}."""
    response = requests.get(
        f"{base_url}/text/{text_id}",
        params={"mode": mode},
        headers={"sabio-auth-token": token},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def summarize(payload: dict[str, Any]) -> None:
    text = (payload.get("data") or {}).get("result") or {}
    print(f"Text:        {text.get('id')}")
    print(f"Title:       {text.get('title')!r}")
    print(f"Tree path:   {text.get('treePath')}")
    print(f"Visible:     {text.get('visible')}")
    print(f"Valid from:  {text.get('validFrom')}")
    print(f"Valid to:    {text.get('validTo')}")

    fragments = text.get("fragments", []) or []
    print(f"\n{len(fragments)} fragment(s):")
    for index, fragment in enumerate(fragments, start=1):
        content = fragment.get("content") or ""
        tags = ", ".join(fragment.get("tags", []) or []) or "-"
        attachments = fragment.get("attachmentCount", 0) or 0
        print(
            f"  {index:>2}. {fragment.get('id')} "
            f"-- {len(content)} chars, "
            f"{attachments} attachment(s), "
            f"tags=[{tags}]"
        )


def main() -> int:
    token = login(BASE_URL, USERNAME, PASSWORD)
    payload = find_text(BASE_URL, token, TEXT_ID, MODE)
    summarize(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
