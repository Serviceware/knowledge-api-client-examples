#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Export a Serviceware Knowledge content view as a static HTML ZIP archive.
#
# This script authenticates against the Knowledge REST API, then downloads
# the content view export in HTML format and saves it to a local file.
#
# Usage:
#   ./export-html.sh
#
# Prerequisites:
#   - curl and jq must be installed
#   - The user must have the BRANCH_EXPORT permission
# ---------------------------------------------------------------------------

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration — adjust these values to match your environment
# ---------------------------------------------------------------------------
BASE_URL="https://<your-instance>/sabio-web/services"
USERNAME="<username>"
PASSWORD="<password>"
CONTENT_VIEW_ID="<content-view-id>"
OUTPUT_FILE="export.zip"

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

# Extract the session token from the JSON response.
# The token is located at .data.key in the response body.
TOKEN=$(echo "${LOGIN_RESPONSE}" | jq -r '.data.key')

if [ -z "${TOKEN}" ] || [ "${TOKEN}" = "null" ]; then
  echo "ERROR: Authentication failed. Response:"
  echo "${LOGIN_RESPONSE}" | jq .
  exit 1
fi

echo "Authentication successful."

# ---------------------------------------------------------------------------
# Step 2: Export the content view as HTML
# ---------------------------------------------------------------------------
echo "Exporting content view ${CONTENT_VIEW_ID} as HTML..."

HTTP_STATUS=$(curl -s -o "${OUTPUT_FILE}" -w "%{http_code}" \
  "${BASE_URL}/branch-export/${CONTENT_VIEW_ID}?type=html" \
  -H "sabio-auth-token: ${TOKEN}")

if [ "${HTTP_STATUS}" -ne 200 ]; then
  echo "ERROR: Export failed with HTTP status ${HTTP_STATUS}."
  echo "Response body:"
  cat "${OUTPUT_FILE}"
  rm -f "${OUTPUT_FILE}"
  exit 1
fi

# ---------------------------------------------------------------------------
# Step 3: Verify and report
# ---------------------------------------------------------------------------
FILE_SIZE=$(wc -c < "${OUTPUT_FILE}" | tr -d ' ')
echo "Export saved to '${OUTPUT_FILE}' (${FILE_SIZE} bytes)."
echo "Done."
