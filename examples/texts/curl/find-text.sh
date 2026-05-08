#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Fetch a single text by ID via GET /text/{id}.
#
# Authenticates with username/password, then retrieves the configured text
# and prints title, treePath, and a summary of its fragments.
#
# Usage:
#   ./find-text.sh
#
# Prerequisites:
#   - curl and jq must be installed
#   - The user must have the TEXT_READ permission and read access to the text
# ---------------------------------------------------------------------------

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL="https://<your-instance>/sabio-web/services"
USERNAME="<username>"
PASSWORD="<password>"

TEXT_ID="<text-id>"
MODE="view"   # "view" or "edit"

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
  echo "ERROR: Authentication failed. Response:"
  echo "${LOGIN_RESPONSE}" | jq .
  exit 1
fi

# ---------------------------------------------------------------------------
# Step 2: Fetch the text
# ---------------------------------------------------------------------------
echo "Fetching text ${TEXT_ID} (mode=${MODE})..."

curl -s -G \
  "${BASE_URL}/text/${TEXT_ID}" \
  -H "sabio-auth-token: ${TOKEN}" \
  --data-urlencode "mode=${MODE}" \
  | jq '{
      id: .data.result.id,
      title: .data.result.title,
      treePath: .data.result.treePath,
      visible: .data.result.visible,
      validFrom: .data.result.validFrom,
      validTo: .data.result.validTo,
      fragmentCount: (.data.result.fragments | length),
      fragments: [.data.result.fragments[] | {
        id,
        tags,
        attachmentCount,
        contentLength: (.content | length)
      }]
    }'
