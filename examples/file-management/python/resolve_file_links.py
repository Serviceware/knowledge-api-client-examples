#!/usr/bin/env python3
"""
Fetch a knowledge text, extract every data-sabio-file-id reference from its
HTML content, and resolve each one to FM metadata + pre-signed URL.

Requires:
    pip install requests beautifulsoup4

Usage:
    python resolve_file_links.py
"""

import sys
from typing import Any

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration -- replace placeholders with values for your environment.
# ---------------------------------------------------------------------------
BASE_URL = "https://<your-instance>/sabio-web/services"
USERNAME = "<username>"
PASSWORD = "<password>"

TEXT_ID = "<text-id>"

FM_FILE_ATTR = "data-sabio-file-id"


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


def fetch_text(base_url: str, token: str, text_id: str) -> dict[str, Any]:
    response = requests.get(
        f"{base_url}/text/{text_id}",
        params={"mode": "view"},
        headers={"sabio-auth-token": token},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def extract_file_ids(text_payload: dict[str, Any]) -> list[str]:
    """Walk all fragments and return the unique set of data-sabio-file-id values."""
    fragments = (text_payload.get("data") or {}).get("result", {}).get("fragments", []) or []
    ids: list[str] = []
    seen: set[str] = set()
    for fragment in fragments:
        content = fragment.get("content") or ""
        if not content:
            continue
        soup = BeautifulSoup(content, "html.parser")
        for element in soup.select(f"[{FM_FILE_ATTR}]"):
            file_id = element.get(FM_FILE_ATTR)
            if file_id and file_id not in seen:
                seen.add(file_id)
                ids.append(file_id)
    return ids


def fetch_metadata(base_url: str, token: str, file_id: str) -> dict[str, Any]:
    response = requests.get(
        f"{base_url}/fm/{file_id}",
        headers={"sabio-auth-token": token},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def fetch_urls(base_url: str, token: str, file_id: str, *, download: bool = False) -> dict[str, Any]:
    response = requests.get(
        f"{base_url}/fm/url/{file_id}",
        params={"download": "true" if download else "false"},
        headers={"sabio-auth-token": token},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


PREVIEW_STATUSES = {"done", "pending", "unsupported", "none"}


def describe_preview(preview: str | None) -> str:
    if not preview:
        return "<missing>"
    if preview in PREVIEW_STATUSES:
        return f"status={preview}"
    return f"url={preview[:80]}..."


def main() -> int:
    token = login(BASE_URL, USERNAME, PASSWORD)
    text_payload = fetch_text(BASE_URL, token, TEXT_ID)

    text = (text_payload.get("data") or {}).get("result") or {}
    print(f"Text:  {text.get('id')}  ({text.get('title')!r})")

    file_ids = extract_file_ids(text_payload)
    if not file_ids:
        print("No file references found in this text.")
        return 0

    print(f"Found {len(file_ids)} unique file reference(s):")
    for index, file_id in enumerate(file_ids, start=1):
        print(f"\n  {index}. {file_id}")
        try:
            meta = (fetch_metadata(BASE_URL, token, file_id).get("data") or {}).get("result") or {}
        except requests.HTTPError as exc:
            print(f"     metadata: HTTP {exc.response.status_code}")
            continue

        print(f"     filename:   {meta.get('filename')}")
        print(f"     mimeType:   {meta.get('mimeType')}")
        print(f"     size:       {meta.get('size')} bytes")
        print(f"     permission: {meta.get('userPermission')}  (bitfield: 1=read 2=create 4=update 8=delete)")

        try:
            urls = (fetch_urls(BASE_URL, token, file_id).get("data") or {}).get("result") or {}
        except requests.HTTPError as exc:
            print(f"     url:        HTTP {exc.response.status_code}")
            continue

        url = urls.get("url") or ""
        print(f"     url:        {url[:80]}{'...' if len(url) > 80 else ''}")
        print(f"     preview:    {describe_preview(urls.get('preview'))}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
