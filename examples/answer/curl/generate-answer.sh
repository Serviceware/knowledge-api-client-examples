#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Generate a grounded AI answer to a natural-language query via the blocking
# POST /ai/answer endpoint.
#
# Usage:
#   ./generate-answer.sh
#
# Prerequisites:
#   - curl and jq must be installed
#   - The user must have read access to at least some knowledge content
# ---------------------------------------------------------------------------

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration -- replace placeholders with values for your environment.
# ---------------------------------------------------------------------------
BASE_URL="https://<your-instance>/sabio-web/services"
USERNAME="<username>"
PASSWORD="<password>"

# Stable identifier for your integration -- appears as the channel name in
# usage reports. Pick something unique to your integration.
CLIENT_NAME="acme-portal"
CLIENT_VERSION="1.0.0"

QUERY="How do I reset my password?"

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
  echo "${LOGIN_RESPONSE}" | jq .
  exit 1
fi

# ---------------------------------------------------------------------------
# Step 2: Build the sabio-client header value
# ---------------------------------------------------------------------------
SABIO_CLIENT=$(jq -nc \
  --arg name "${CLIENT_NAME}" \
  --arg version "${CLIENT_VERSION}" \
  '{name: $name, version: $version}')

# ---------------------------------------------------------------------------
# Step 3: Request the answer
# ---------------------------------------------------------------------------
echo "Asking: ${QUERY}"
echo

RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/ai/answer" \
  -H "Content-Type: application/json" \
  -H "sabio-auth-token: ${TOKEN}" \
  -H "sabio-client: ${SABIO_CLIENT}" \
  -d "$(jq -nc --arg query "${QUERY}" '{query: $query}')")

# ---------------------------------------------------------------------------
# Step 4: Render
# ---------------------------------------------------------------------------
echo "--- Answer ---"
echo "${RESPONSE}" | jq -r '.data.result.answer'
echo
echo "--- Sources ---"
echo "${RESPONSE}" | jq -r '.data.result.sources[] | "  \(.id)  \(.resource)  \(.title)"'
echo
echo "--- success ---"
echo "${RESPONSE}" | jq '.data.result.success'
