#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Generate a grounded AI answer and stream the response as Server-Sent Events
# via POST /ai/answer/sse. Each event is printed as it arrives.
#
# Usage:
#   ./generate-answer-sse.sh
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

CLIENT_NAME="acme-portal"
CLIENT_VERSION="1.0.0"

QUERY="How do I reset my password?"

# ---------------------------------------------------------------------------
# Step 1: Authenticate
# ---------------------------------------------------------------------------
LOGIN_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/authentication/credentials" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "{
    \"login\": \"${USERNAME}\",
    \"key\": \"${PASSWORD}\"
  }")

TOKEN=$(echo "${LOGIN_RESPONSE}" | jq -r '.data.key')

if [ -z "${TOKEN}" ] || [ "${TOKEN}" = "null" ]; then
  echo "ERROR: Authentication failed." >&2
  exit 1
fi

SABIO_CLIENT=$(jq -nc \
  --arg name "${CLIENT_NAME}" \
  --arg version "${CLIENT_VERSION}" \
  '{name: $name, version: $version}')

# ---------------------------------------------------------------------------
# Step 2: Open the SSE stream and parse events as they arrive
#
# SSE format:
#   event: <name>
#   data: <json>
#   <blank line marks end of event>
# ---------------------------------------------------------------------------
echo "Asking: ${QUERY}"
echo

curl -sN -X POST \
  "${BASE_URL}/ai/answer/sse" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -H "sabio-auth-token: ${TOKEN}" \
  -H "sabio-client: ${SABIO_CLIENT}" \
  -d "$(jq -nc --arg query "${QUERY}" '{query: $query}')" \
| awk '
    BEGIN { event=""; data="" }
    /^event:/    { event=substr($0, 8); next }
    /^data:/     { data=data substr($0, 7); next }
    /^[[:space:]]*$/ {
        if (event != "") {
            print "--- " event " ---"
            print data
            event=""; data=""
        }
        next
    }
'
