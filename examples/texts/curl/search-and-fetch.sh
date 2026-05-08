#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Search texts via POST /text/search, then fetch the top hit via GET /text/{id}.
#
# Demonstrates the typical "search to discover, fetch to read" pattern.
#
# Usage:
#   ./search-and-fetch.sh
#
# Prerequisites:
#   - curl and jq must be installed
#   - The user must have the TEXT_READ permission
# ---------------------------------------------------------------------------

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL="https://<your-instance>/sabio-web/services"
USERNAME="<username>"
PASSWORD="<password>"

QUERY="vacation policy"
LIMIT=5

# ---------------------------------------------------------------------------
# Step 1: Authenticate
# ---------------------------------------------------------------------------
echo "Authenticating as '${USERNAME}'..."

LOGIN_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/authentication/credentials" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "{
    \"login\": \"${USERNAME}\",
    \"key\": \"${PASSWORD}\"
  }")

TOKEN=$(echo "${LOGIN_RESPONSE}" | jq -r '.data.key')

if [ -z "${TOKEN}" ] || [ "${TOKEN}" = "null" ]; then
  echo "ERROR: Authentication failed."
  exit 1
fi

# ---------------------------------------------------------------------------
# Step 2: Search texts
# ---------------------------------------------------------------------------
echo "Searching texts for '${QUERY}'..."

SEARCH_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/text/search" \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "sabio-auth-token: ${TOKEN}" \
  -d "$(jq -n \
        --arg query "${QUERY}" \
        --argjson limit "${LIMIT}" \
        '{
           query: $query,
           limit: $limit,
           fields: ["id", "title", "score", "lastModified", "excerpt"]
         }')")

TOTAL=$(echo "${SEARCH_RESPONSE}" | jq -r '.data.total')
TOP_ID=$(echo "${SEARCH_RESPONSE}" | jq -r '.data.result[0].id // empty')

echo "${SEARCH_RESPONSE}" | jq '{
  total: .data.total,
  hits: [.data.result[] | {id, title, score}]
}'

if [ -z "${TOP_ID}" ]; then
  echo "No hits — nothing to fetch."
  exit 0
fi

# ---------------------------------------------------------------------------
# Step 3: Fetch the top hit
# ---------------------------------------------------------------------------
echo
echo "Fetching top hit ${TOP_ID}..."

curl -s -G \
  "${BASE_URL}/text/${TOP_ID}" \
  -H "sabio-auth-token: ${TOKEN}" \
  --data-urlencode "mode=view" \
  | jq '{
      id: .data.result.id,
      title: .data.result.title,
      treePath: .data.result.treePath,
      fragmentCount: (.data.result.fragments | length)
    }'
