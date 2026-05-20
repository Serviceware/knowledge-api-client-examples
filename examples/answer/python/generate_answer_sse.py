#!/usr/bin/env python3
"""
Generate a grounded AI answer via the streaming POST /ai/answer/sse endpoint.

Prints each SSE event as it arrives and reconstructs the full answer from
the incremental `answer` event chunks.

Requires:
    pip install requests

Usage:
    python generate_answer_sse.py
"""

import json
import sys
from typing import Any, Generator

import requests

# ---------------------------------------------------------------------------
# Configuration -- replace placeholders with values for your environment.
# ---------------------------------------------------------------------------
BASE_URL = "https://<your-instance>/sabio-web/services"
USERNAME = "<username>"
PASSWORD = "<password>"

CLIENT_NAME = "acme-portal"
CLIENT_VERSION = "1.0.0"

QUERY = "How do I reset my password?"


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


def stream_events(base_url: str, token: str, query: str) -> Generator[tuple[str, dict[str, Any]], None, None]:
    """Yield (event_name, parsed_data) tuples as they arrive from the SSE stream."""
    response = requests.post(
        f"{base_url}/ai/answer/sse",
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "sabio-auth-token": token,
            "sabio-client": sabio_client_header(),
        },
        json={"query": query},
        stream=True,
        timeout=(30, 120),
    )
    response.raise_for_status()

    event_name = ""
    data_lines: list[str] = []

    for raw_line in response.iter_lines(decode_unicode=True):
        if raw_line is None:
            continue
        line = raw_line.rstrip("\r")

        if line == "":
            # Blank line terminates an event.
            if event_name and data_lines:
                data_str = "\n".join(data_lines)
                try:
                    yield event_name, json.loads(data_str)
                except json.JSONDecodeError:
                    yield event_name, {"raw": data_str}
            event_name = ""
            data_lines = []
            continue

        if line.startswith(":"):
            # Comment line; ignore.
            continue
        if line.startswith("event:"):
            event_name = line[6:].lstrip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())


def main() -> int:
    token = login(BASE_URL, USERNAME, PASSWORD)

    print(f"Question: {QUERY}\n")
    answer_chunks: list[str] = []
    sources: list[dict[str, Any]] = []

    for event_name, data in stream_events(BASE_URL, token, QUERY):
        if event_name == "sources":
            sources = data.get("sources") or []
            print(f"--- sources ({len(sources)}) ---")
            for source in sources:
                print(f"  {source.get('id')}  {source.get('resource')}  {source.get('title')}")
            print()
            print("--- answer (streaming) ---")
        elif event_name == "answer":
            chunk = data.get("answer") or ""
            answer_chunks.append(chunk)
            sys.stdout.write(chunk)
            sys.stdout.flush()
        elif event_name == "done":
            print()
            print()
            print(f"--- done (success={data.get('success')}) ---")
            break
        elif event_name == "error":
            print()
            error = data.get("error") or {}
            print(f"--- error: code={error.get('code')} text={error.get('text')!r} ---", file=sys.stderr)
            return 1

    full_answer = "".join(answer_chunks)
    print(f"\nReconstructed answer length: {len(full_answer)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
