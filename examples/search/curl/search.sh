#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Search the Serviceware Knowledge instance via POST /search.
#
# Authenticates with username/password, then issues a single search request
# and prints the raw JSON response.
#
# Usage:
#   ./search.sh
#
# Prerequisites:
#   - curl and jq must be installed
#   - The user must have the SEARCH_READ permission
# ---------------------------------------------------------------------------

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL="https://<your-instance>/sabio-web/services"
USERNAME="<username>"
PASSWORD="<password>"
QUERY="vacation policy"
LIMIT=10

# ---------------------------------------------------------------------------
# Step 1: Authenticate and obtain a session token
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
  echo "ERROR: Authentication failed. Response:"
  echo "${LOGIN_RESPONSE}" | jq .
  exit 1
fi

# ---------------------------------------------------------------------------
# Step 2: Run the search
# ---------------------------------------------------------------------------
echo "Searching for '${QUERY}'..."

curl -s -X POST \
  "${BASE_URL}/search" \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "sabio-auth-token: ${TOKEN}" \
  -d "$(jq -n \
        --arg query "${QUERY}" \
        --argjson limit "${LIMIT}" \
        '{
           query: $query,
           limit: $limit,
           fields: ["id", "title", "resource", "score", "lastModified"]
         }')" \
  | jq '{
      total: .data.total,
      queryTerm: .data.queryTerm,
      hits: [.data.result[] | {id, resource, title, score}]
    }'
